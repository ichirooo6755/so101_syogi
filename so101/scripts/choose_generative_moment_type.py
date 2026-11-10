import adsk.core
import adsk.fusion
import builtins
assert ui.activeCommand=='GenLoadsCommand'
print(app.executeTextCommand('Commands.SetString infoSimLoadsType SimMomentLoadCommand'))
