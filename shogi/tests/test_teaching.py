"""Manual teaching records stable measurements and never performs playback."""
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import teach_capture
import teach_store


class TeachingStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.directory=Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.capture={'calibration_verified':True,'calibration_sha256':'a'*64,'follower_usb_id':'f'*64,
                      'positions':{name:(40 if name=='gripper' else 1.) for name in teach_store.NAMES},
                      'torque_enabled':{name:False for name in teach_store.NAMES}}

    def test_four_phases_saved_and_remain_unverified(self):
        session=teach_store.begin('9e','white',{'x':.19},self.directory,mode='manual')
        for _ in range(4):
            session=teach_store.add_capture(session,self.capture,self.directory)
        self.assertEqual(session['status'],'recorded_unverified')
        self.assertEqual([x['phase'] for x in session['samples']],
                         ['approach','align','grasp','lift'])
        self.assertFalse(session['physical_board_pose_verified'])
        saved=json.loads((self.directory/(session['id']+'.json')).read_text())
        self.assertEqual(saved,session)
        with self.assertRaises(ValueError): teach_store.add_capture(session,self.capture,self.directory)

    def test_changed_calibration_and_bad_positions_do_not_update_file(self):
        session=teach_store.begin('1a','black',{},self.directory,mode='manual')
        session=teach_store.add_capture(session,self.capture,self.directory)
        path=self.directory/(session['id']+'.json'); original=path.read_bytes()
        for bad in ({**self.capture,'calibration_sha256':'b'*64},
                    {**self.capture,'positions':{**self.capture['positions'],'shoulder_pan':float('nan')}},
                    {**self.capture,'calibration_verified':False}):
            with self.assertRaises(ValueError): teach_store.add_capture(session,bad,self.directory)
            self.assertEqual(path.read_bytes(),original)

    def test_square_and_side_are_validated(self):
        for square,side in (('../x','black'),('9j','black'),('9a','unknown')):
            with self.assertRaises(ValueError): teach_store.begin(square,side,{},self.directory)

    def test_leader_session_requires_and_saves_both_verified_arms(self):
        session=teach_store.begin('9e','white',{},self.directory,mode='leader')
        with self.assertRaises(ValueError): teach_store.add_capture(session,self.capture,self.directory)
        paired={**self.capture,'leader_positions':dict(self.capture['positions']), 'leader_usb_id':'e'*64,
                'leader_calibration_sha256':'b'*64,'leader_calibration_verified':True}
        session=teach_store.add_capture(session,paired,self.directory)
        self.assertEqual(session['samples'][0]['leader_positions'],paired['leader_positions'])
        self.assertEqual(session['leader_calibration_sha256'],'b'*64)
        with self.assertRaises(ValueError):
            teach_store.add_capture(session,{**paired,'leader_calibration_sha256':'c'*64},self.directory)

    def test_placing_is_taught_with_its_own_phases(self):
        session=teach_store.begin('7f','white',{},self.directory,mode='manual',operation='place',
                                  issue={'evidence':'simulated_placement'})
        for _ in range(4): session=teach_store.add_capture(session,self.capture,self.directory)
        self.assertEqual([x['phase'] for x in session['samples']],
                         ['approach_loaded','align_loaded','release','retreat'])
        self.assertEqual(session['failure_context']['evidence'],'simulated_placement')
        self.assertEqual(session['arm'],'stock')


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.port=Path(self.temp.name)/'device';self.port.touch()
        self.calib=Path(self.temp.name)/'calib.json';self.calib.write_text('{}')
        self.leader_calib=Path(self.temp.name)/'leader.json'
        self.leader_calib.write_text(json.dumps({n:{'id':i} for i,n in enumerate(teach_capture.NAMES,1)}))
        self.instances=[]
        owner=self

        class FakeFollower:
            def __init__(self,port):
                self.is_connected=False;self.is_calibrated=True;self.reads=0;self.closed=False
                self.calibration={n:types.SimpleNamespace(id=i) for i,n in enumerate(teach_capture.NAMES,1)}
                self.port=types.SimpleNamespace(ser=types.SimpleNamespace(fileno=lambda:23))
                owner.instances.append(self)
            def connect(self): self.is_connected=True
            def disconnect(self): self.closed=True;self.is_connected=False
            def read(self,*args,**kwargs): return 0
            def _read(self,*args): return 0
            def sync_read(self,*args,**kwargs):
                self.reads+=1
                return {n:(20. if n=='gripper' else 0.) for n in teach_capture.NAMES}
        self.fake=FakeFollower

    def run_snapshot(self,holders=(set(),set()),leader_port=None):
        module=types.SimpleNamespace(Follower=self.fake)
        with patch.dict(sys.modules,{'follower_pad_bus':module}), \
             patch.object(teach_capture,'CALIB',self.calib), \
             patch.object(teach_capture,'LEADER_CALIB',self.leader_calib), \
             patch.object(teach_capture,'validate_ports',side_effect=lambda ports:['f'*64,'e'*64][:len(ports)]), \
             patch.object(teach_capture,'port_holders',side_effect=holders), \
             patch.object(teach_capture.fcntl,'ioctl'), \
             patch.object(teach_capture.time,'sleep'):
            return teach_capture.read_snapshot(str(self.port),leader_port)

    def test_stable_snapshot_reads_six_and_disconnects(self):
        result=self.run_snapshot()
        self.assertEqual(set(result['positions']),set(teach_capture.NAMES))
        self.assertTrue(result['calibration_verified'])
        self.assertEqual(self.instances[0].reads,3)
        self.assertTrue(self.instances[0].closed)

    def test_existing_owner_is_rejected_before_open(self):
        with self.assertRaisesRegex(ValueError,'切断'):
            self.run_snapshot(holders=({123},))
        self.assertEqual(self.instances,[])

    def test_owner_race_is_rejected_and_port_closed(self):
        with self.assertRaisesRegex(ValueError,'他のアプリ'):
            self.run_snapshot(holders=(set(),{123}))
        self.assertTrue(self.instances[0].closed)

    def test_paired_snapshot_reads_and_closes_both_arms(self):
        result=self.run_snapshot(holders=(set(),set(),set(),set()),leader_port='leader-port')
        self.assertEqual(set(result['leader_positions']),set(teach_capture.NAMES))
        self.assertTrue(result['leader_calibration_verified'])
        self.assertEqual(len(self.instances),2)
        self.assertTrue(all(i.closed and i.reads==3 for i in self.instances))

    def test_motion_is_rejected(self):
        original=self.fake.sync_read
        def moving(instance,*args,**kwargs):
            values=original(instance,*args,**kwargs)
            values['shoulder_pan']=instance.reads*1.1
            return values
        self.fake.sync_read=moving
        with self.assertRaisesRegex(ValueError,'動いています'):
            self.run_snapshot()
        self.assertTrue(self.instances[0].closed)

    def test_usb_aliases_with_same_serial_are_rejected(self):
        fake=[types.SimpleNamespace(device='/dev/cu.one',vid=1,pid=2,serial_number='same',location='A'),
              types.SimpleNamespace(device='/dev/cu.two',vid=1,pid=2,serial_number='same',location='B')]
        with patch('serial.tools.list_ports.comports',return_value=fake):
            with self.assertRaisesRegex(ValueError,'同じ USB'):
                teach_capture.validate_ports(['/dev/cu.one','/dev/cu.two'])


if __name__=='__main__': unittest.main()
