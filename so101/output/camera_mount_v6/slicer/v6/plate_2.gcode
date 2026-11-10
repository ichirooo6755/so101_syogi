; HEADER_BLOCK_START
; BambuStudio 02.08.02.61
; model printing time: 18m 34s; total estimated time: 24m 50s
; total layer number: 79
; total filament length [mm] : 2076.84
; total filament volume [cm^3] : 4995.39
; total filament weight [g] : 6.19
; filament_density: 1.24
; filament_diameter: 1.75
; max_z_height: 15.80
; filament: 1
; support_material_on_wipe_tower: 0
; HEADER_BLOCK_END

; CONFIG_BLOCK_START
; accel_to_decel_enable = 0
; accel_to_decel_factor = 50%
; activate_air_filtration = 0
; additional_cooling_fan_speed = 70
; additional_fan_full_speed_layer = 0
; alternate_extra_wall = 0
; ams_filament_load_time_ams = 0
; ams_filament_load_time_ams_lite = 0
; ams_filament_load_time_n3f_s = 0
; ams_filament_unload_time_ams = 0
; ams_filament_unload_time_ams_lite = 0
; ams_filament_unload_time_n3f_s = 0
; apply_scarf_seam_on_circles = 1
; auxiliary_fan = 0
; avoid_crossing_wall_includes_support = 0
; bed_custom_model = 
; bed_custom_texture = 
; bed_exclude_area = 
; bed_heat_soak_area = 
; bed_temperature_formula = by_first_filament
; before_layer_change_gcode = 
; best_object_pos = 0.7,0.5
; bottom_color_penetration_layers = 3
; bottom_shell_layers = 6
; bottom_shell_thickness = 0
; bottom_surface_density = 100%
; bottom_surface_pattern = monotonic
; bridge_angle = 0
; bridge_flow = 1
; bridge_no_support = 1
; bridge_speed = 50
; brim_object_gap = 0.1
; brim_type = outer_only
; brim_width = 5
; chamber_temperatures = 0
; change_filament_gcode = ;===== A1mini 20251031 =====\nG392 S0\nM1007 S0\nM620 S[next_extruder]A\nM204 S9000\nG1 Z{max_layer_z + 3.0} F1200\n\nM400\nM106 P1 S0\nM106 P2 S0\n{if old_filament_temp > 142 && next_extruder < 255}\nM104 S[old_filament_temp]\n{endif}\n\nG1 X180 F18000\n\n{if long_retractions_when_cut[previous_extruder]}\nM620.11 S1 I[previous_extruder] E-{retraction_distances_when_cut[previous_extruder]} F1200\n{else}\nM620.11 S0\n{endif}\nM400\n\nM620.1 E F{flush_volumetric_speeds[previous_extruder]/2.4053*60} T{flush_temperatures[previous_extruder]}\nM620.10 A0 F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\nT[next_extruder]\nM620.1 E F{flush_volumetric_speeds[next_extruder]/2.4053*60} T{flush_temperatures[next_extruder]}\nM620.10 A1 F{flush_volumetric_speeds[next_extruder]/2.4053*60} L[flush_length] H[nozzle_diameter] T{flush_temperatures[next_extruder]}\n\nG1 Y90 F9000\n\n{if next_extruder < 255}\n\n{if long_retractions_when_cut[previous_extruder]}\nM620.11 S1 I[previous_extruder] E{retraction_distances_when_cut[previous_extruder]} F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\nM628 S1\nG92 E0\nG1 E{retraction_distances_when_cut[previous_extruder]} F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\nM400\nM629 S1\n{else}\nM620.11 S0\n{endif}\n\nM400\nG92 E0\nM628 S0\n\n{if flush_length_1 > 1}\n; FLUSH_START\n; always use highest temperature to flush\nM400\nM1002 set_filament_type:UNKNOWN\nM109 S[flush_temperatures[next_extruder]]\nM106 P1 S60\n{if flush_length_1 > 23.7}\nG1 E23.7 F{flush_volumetric_speeds[previous_extruder]/2.4053*60} ; do not need pulsatile flushing for start part\nG1 E{(flush_length_1 - 23.7) * 0.02} F50\nG1 E{(flush_length_1 - 23.7) * 0.23} F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\nG1 E{(flush_length_1 - 23.7) * 0.02} F50\nG1 E{(flush_length_1 - 23.7) * 0.23} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{(flush_length_1 - 23.7) * 0.02} F50\nG1 E{(flush_length_1 - 23.7) * 0.23} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{(flush_length_1 - 23.7) * 0.02} F50\nG1 E{(flush_length_1 - 23.7) * 0.23} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\n{else}\nG1 E{flush_length_1} F{flush_volumetric_speeds[previous_extruder]/2.4053*60}\n{endif}\n; FLUSH_END\nG1 E-[old_retract_length_toolchange] F1800\nG1 E[old_retract_length_toolchange] F300\nM400\nM1002 set_filament_type:{filament_type[next_extruder]}\n{endif}\n\n{if flush_length_1 > 45 && flush_length_2 > 1}\n; WIPE\nM400\nM106 P1 S178\nM400 S3\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nM400\nM106 P1 S0\n{endif}\n\n{if flush_length_2 > 1}\nM106 P1 S60\n; FLUSH_START\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\nG1 E{flush_length_2 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_2 * 0.02} F50\n; FLUSH_END\nG1 E-[new_retract_length_toolchange] F1800\nG1 E[new_retract_length_toolchange] F300\n{endif}\n\n{if flush_length_2 > 45 && flush_length_3 > 1}\n; WIPE\nM400\nM106 P1 S178\nM400 S3\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nM400\nM106 P1 S0\n{endif}\n\n{if flush_length_3 > 1}\nM106 P1 S60\n; FLUSH_START\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\nG1 E{flush_length_3 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_3 * 0.02} F50\n; FLUSH_END\nG1 E-[new_retract_length_toolchange] F1800\nG1 E[new_retract_length_toolchange] F300\n{endif}\n\n{if flush_length_3 > 45 && flush_length_4 > 1}\n; WIPE\nM400\nM106 P1 S178\nM400 S3\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nM400\nM106 P1 S0\n{endif}\n\n{if flush_length_4 > 1}\nM106 P1 S60\n; FLUSH_START\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\nG1 E{flush_length_4 * 0.18} F{flush_volumetric_speeds[next_extruder]/2.4053*60}\nG1 E{flush_length_4 * 0.02} F50\n; FLUSH_END\n{endif}\n\nM629\n\nM400\nM106 P1 S60\nM109 S[new_filament_temp]\nG1 E5 F{flush_volumetric_speeds[next_extruder]/2.4053*60} ;Compensate for filament spillage during waiting temperature\nM400\nG92 E0\nG1 E-[new_retract_length_toolchange] F1800\nM400\nM106 P1 S178\nM400 S3\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nG1 X-3.5 F18000\nG1 X-13.5 F3000\nM400\nG1 Z{max_layer_z + 3.0} F3000\nM106 P1 S0\n{if layer_z <= (initial_layer_print_height + 0.001)}\nM204 S[initial_layer_acceleration]\n{else}\nM204 S[default_acceleration]\n{endif}\n{else}\nG1 X[x_after_toolchange] Y[y_after_toolchange] Z[z_after_toolchange] F12000\n{endif}\n\nM622.1 S0\nM9833 F{outer_wall_volumetric_speed/2.4} A0.3 ; cali dynamic extrusion compensation\nM1002 judge_flag filament_need_cali_flag\nM622 J1\n  G92 E0\n  G1 E-[new_retract_length_toolchange] F1800\n  M400\n  \n  M106 P1 S178\n  M400 S7\n  G1 X0 F18000\n  G1 X-13.5 F3000\n  G1 X0 F18000 ;wipe and shake\n  G1 X-13.5 F3000\n  G1 X0 F12000 ;wipe and shake\n  G1 X-13.5 F3000\n  G1 X0 F12000 ;wipe and shake\n  M400\n  M106 P1 S0 \nM623\n\nM621 S[next_extruder]A\nG392 S0\n\nM1007 S1\n
; circle_compensation_manual_offset = 0
; circle_compensation_speed = 200
; close_additional_fan_first_x_layers = 1
; close_fan_the_first_x_layers = 1
; compatible_printers_condition = 
; complete_print_exhaust_fan_speed = 70
; cool_plate_temp = 35
; cool_plate_temp_initial_layer = 35
; cooling_filter_enabled = 0
; cooling_perimeter_transition_distance = 10
; cooling_slowdown_logic = uniform_cooling
; counter_coef_1 = 0
; counter_coef_2 = 0.008
; counter_coef_3 = -0.041
; counter_limit_max = 0.033
; counter_limit_min = -0.035
; counterbore_hole_bridging = none
; curr_bed_type = Textured PEI Plate
; default_acceleration = 6000
; default_ams_type = -1
; default_filament_colour = ""
; default_filament_profile = "Bambu PLA Basic @BBL A1M"
; default_jerk = 0
; default_nozzle_volume_type = Standard
; default_print_profile = 0.20mm Standard @BBL A1M
; deretraction_speed = 30
; detect_floating_vertical_shell = 1
; detect_narrow_internal_solid_infill = 1
; detect_overhang_wall = 1
; detect_thin_wall = 0
; diameter_limit = 50
; different_settings_to_system = ;;
; draft_shield = disabled
; during_print_exhaust_fan_speed = 70
; elefant_foot_compensation = 0
; embedding_wall_into_infill = 0
; enable_arc_fitting = 1
; enable_circle_compensation = 0
; enable_filament_dynamic_map = 0
; enable_height_slowdown = 0
; enable_long_retraction_when_cut = 2
; enable_mixed_color_sublayer = 0
; enable_order_independent_overlap_carving = 0
; enable_overhang_bridge_fan = 1
; enable_overhang_speed = 1
; enable_pre_heating = 0
; enable_pressure_advance = 0
; enable_prime_tower = 0
; enable_support = 1
; enable_support_ironing = 0
; enable_tower_interface_features = 0
; enable_wrapping_detection = 0
; enforce_support_layers = 0
; eng_plate_temp = 0
; eng_plate_temp_initial_layer = 0
; ensure_vertical_shell_thickness = enabled
; exclude_object = 1
; extruder_ams_count = 
; extruder_clearance_dist_to_rod = 56.5
; extruder_clearance_height_to_lid = 180
; extruder_clearance_height_to_rod = 25
; extruder_clearance_max_radius = 73
; extruder_colour = #018001
; extruder_max_nozzle_count = 1
; extruder_nozzle_stats = 
; extruder_offset = 0x0
; extruder_printable_area = 
; extruder_type = Direct Drive
; extruder_variant_list = "Direct Drive Standard"
; fan_cooling_layer_time = 80
; fan_direction = undefine
; fan_max_speed = 80
; fan_min_speed = 60
; farthest_point_timelapse = 0
; filament_adaptive_volumetric_speed = 0
; filament_adhesiveness_category = 100
; filament_bridge_speed = 25
; filament_change_length = 10
; filament_change_length_nc = 10
; filament_colour = #00AE42
; filament_cooling_before_tower = 0
; filament_cost = 20
; filament_density = 1.24
; filament_dev_ams_drying_ams_limitations = 1
; filament_dev_ams_drying_heat_distortion_temperature = 45
; filament_dev_ams_drying_temperature = 45
; filament_dev_ams_drying_time = 12
; filament_dev_chamber_drying_bed_temperature = 70
; filament_dev_chamber_drying_time = 12
; filament_dev_drying_cooling_temperature = 45
; filament_dev_drying_softening_temperature = 50
; filament_diameter = 1.75
; filament_enable_overhang_speed = 1
; filament_end_gcode = "; filament end gcode \n\n"
; filament_extruder_compatibility = 0
; filament_extruder_variant = "Direct Drive Standard"
; filament_flow_ratio = 0.98
; filament_flush_temp = 0
; filament_flush_temp_fast = 0
; filament_flush_volumetric_speed = 0
; filament_ids = GFL99
; filament_is_mixed = 0
; filament_is_support = 0
; filament_map = 1
; filament_map_2 = 0
; filament_map_mode = Auto For Flush
; filament_max_volumetric_speed = 12
; filament_metal_stickiness = None
; filament_minimal_purge_on_wipe_tower = 15
; filament_mixed_components = ""
; filament_mixed_gradient = 0
; filament_mixed_gradient_curve = ""
; filament_mixed_gradient_per_part = 0
; filament_mixed_gradient_range = ""
; filament_mixed_sublayer_ratios = ""
; filament_notes = 
; filament_nozzle_map = 0
; filament_overhang_1_4_speed = 0
; filament_overhang_2_4_speed = 50
; filament_overhang_3_4_speed = 30
; filament_overhang_4_4_speed = 10
; filament_overhang_totally_speed = 10
; filament_pre_cooling_temperature = 0
; filament_pre_cooling_temperature_nc = 0
; filament_preheat_temperature_delta = 0
; filament_prime_volume = 45
; filament_prime_volume_nc = 60
; filament_printable = 3
; filament_ramming_travel_time = 0
; filament_ramming_travel_time_nc = 0
; filament_ramming_volumetric_speed = -1
; filament_ramming_volumetric_speed_nc = -1
; filament_retract_length_nc = 14
; filament_scarf_gap = 15%
; filament_scarf_height = 10%
; filament_scarf_length = 10
; filament_scarf_seam_type = none
; filament_self_index = 1
; filament_settings_id = "Generic PLA @BBL A1M"
; filament_shrink = 100%
; filament_soluble = 0
; filament_start_gcode = "; filament start gcode\n{if  (bed_temperature[current_extruder] >45)||(bed_temperature_initial_layer[current_extruder] >45)}M106 P3 S255\n{elsif(bed_temperature[current_extruder] >35)||(bed_temperature_initial_layer[current_extruder] >35)}M106 P3 S180\n{endif};Prevent PLA from jamming\n\n\n{if activate_air_filtration[current_extruder] && support_air_filtration}\nM106 P3 S{during_print_exhaust_fan_speed_num[current_extruder]} \n{endif}"
; filament_tower_interface_pre_extrusion_dist = 10
; filament_tower_interface_pre_extrusion_length = 0
; filament_tower_interface_print_temp = -1
; filament_tower_interface_purge_volume = 20
; filament_tower_ironing_area = 4
; filament_type = PLA
; filament_velocity_adaptation_factor = 1
; filament_vendor = Generic
; filament_volume_map = 0
; filename_format = {input_filename_base}_{filament_type[0]}_{print_time}.gcode
; fill_multiline = 1
; filter_out_gap_fill = 0
; first_layer_print_sequence = 0
; first_x_layer_fan_speed = 0
; first_x_layer_part_fan_speed = 0
; flush_into_infill = 0
; flush_into_objects = 0
; flush_into_support = 1
; flush_multiplier = 1
; flush_multiplier_fast = 1.2
; flush_volumes_matrix = 0,280,280,280,280,0,280,280,280,280,0,280,280,280,280,0
; flush_volumes_vector = 140,140,140,140,140,140,140,140
; full_fan_speed_layer = 0
; fuzzy_skin = none
; fuzzy_skin_first_layer = 0
; fuzzy_skin_mode = displacement
; fuzzy_skin_noise_type = classic
; fuzzy_skin_octaves = 4
; fuzzy_skin_persistence = 0.5
; fuzzy_skin_point_distance = 0.8
; fuzzy_skin_scale = 1
; fuzzy_skin_thickness = 0.3
; gap_infill_speed = 250
; gcode_add_line_number = 0
; gcode_flavor = marlin
; grab_length = 17.4
; group_algo_with_time = 0
; has_filament_switcher = 0
; has_scarf_joint_seam = 0
; head_wrap_detect_zone = 156x152,180x152,180x180,156x180
; hole_coef_1 = 0
; hole_coef_2 = -0.008
; hole_coef_3 = 0.23415
; hole_limit_max = 0.22
; hole_limit_min = 0.088
; hot_plate_temp = 60
; hot_plate_temp_initial_layer = 60
; hotend_cooling_rate = 2
; hotend_heating_rate = 2
; impact_strength_z = 10
; independent_support_layer_height = 1
; infill_combination = 0
; infill_direction = 45
; infill_instead_top_bottom_surfaces = 0
; infill_jerk = 9
; infill_lock_depth = 1
; infill_rotate_step = 0
; infill_shift_step = 0.4
; infill_wall_overlap = 15%
; inherits_group = ;;
; initial_layer_acceleration = 500
; initial_layer_flow_ratio = 1
; initial_layer_infill_speed = 105
; initial_layer_jerk = 9
; initial_layer_line_width = 0.5
; initial_layer_print_height = 0.2
; initial_layer_speed = 50
; initial_layer_travel_acceleration = 6000
; inner_wall_acceleration = 0
; inner_wall_jerk = 9
; inner_wall_line_width = 0.45
; inner_wall_speed = 300
; interface_shells = 0
; interlocking_beam = 0
; interlocking_beam_layer_count = 2
; interlocking_beam_width = 0.8
; interlocking_boundary_avoidance = 2
; interlocking_depth = 2
; interlocking_orientation = 22.5
; internal_bridge_support_thickness = 0.8
; internal_solid_infill_line_width = 0.42
; internal_solid_infill_pattern = zig-zag
; internal_solid_infill_speed = 250
; ironing_direction = 45
; ironing_fan_speed = -1
; ironing_flow = 10%
; ironing_inset = 0.21
; ironing_pattern = zig-zag
; ironing_spacing = 0.15
; ironing_speed = 30
; ironing_type = no ironing
; is_infill_first = 0
; layer_change_gcode = ; layer num/total_layer_count: {layer_num+1}/[total_layer_count]\n; update layer progress\nM73 L{layer_num+1}\nM991 S0 P{layer_num} ;notify layer change
; layer_height = 0.2
; line_width = 0.42
; locked_skeleton_infill_pattern = zigzag
; locked_skin_infill_pattern = crosszag
; long_retractions_when_cut = 0
; long_retractions_when_ec = 0
; machine_bed_mass_Y = 0
; machine_end_gcode = ;===== date: 20260513 =====================\n;turn off nozzle clog detect\nG392 S0\n\nM400 ; wait for buffer to clear\nG92 E0 ; zero the extruder\nG90\nG1 Z{max_layer_z + 0.4} F900 ; lower z a little\nG1 X0 Y{first_layer_center_no_wipe_tower[1]} F18000 ; move to safe pos\nG1 X-13.0 F3000 ; move to safe pos\n{if !spiral_mode && print_sequence != \"by object\"}\nM1002 judge_flag timelapse_record_flag\nM622 J1\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM400 P100\nM971 S11 C11 O0\nM991 S0 P-1 ;end timelapse at safe pos\nM623\n{endif}\n\nM140 S0 ; turn off bed\nM106 S0 ; turn off fan\nM106 P2 S0 ; turn off remote part cooling fan\nM106 P3 S0 ; turn off chamber cooling fan\n\n;G1 X27 F15000 ; wipe\n\n; pull back filament to AMS\nM620 S255\nG1 X181 F12000\nT255\nG1 X0 F18000\nG1 X-13.0 F3000\nG1 X0 F18000 ; wipe\nM621 S255\n\nM104 S0 ; turn off hotend\n\nM400 ; wait all motion done\nM17 S\nM17 Z0.4 ; lower z motor current to reduce impact if there is something in the bottom\n{if (max_layer_z + 100.0) < 180}\n    G1 Z{max_layer_z + 100.0} F600\n    G1 Z{max_layer_z +98.0}\n{else}\n    G1 Z180 F600\n    G1 Z180\n{endif}\nM400 P100\nM17 R ; restore z current\n\nG90\nG1 X-13 Y180 F3600\n\nG91\nG1 Z-1 F600\nG90\nM83\n\nM220 S100  ; Reset feedrate magnitude\nM201.2 K1.0 ; Reset acc magnitude\nM73.2   R1.0 ;Reset left time magnitude\nM1002 set_gcode_claim_speed_level : 0\n\n;=====printer finish  sound=========\nM17\nM400 S1\nM1006 S1\nM1006 A0 B20 L100 C37 D20 M100 E42 F20 N100\nM1006 A0 B10 L100 C44 D10 M100 E44 F10 N100\nM1006 A0 B10 L100 C46 D10 M100 E46 F10 N100\nM1006 A44 B20 L100 C39 D20 M100 E48 F20 N100\nM1006 A0 B10 L100 C44 D10 M100 E44 F10 N100\nM1006 A0 B10 L100 C0 D10 M100 E0 F10 N100\nM1006 A0 B10 L100 C39 D10 M100 E39 F10 N100\nM1006 A0 B10 L100 C0 D10 M100 E0 F10 N100\nM1006 A0 B10 L100 C44 D10 M100 E44 F10 N100\nM1006 A0 B10 L100 C0 D10 M100 E0 F10 N100\nM1006 A0 B10 L100 C39 D10 M100 E39 F10 N100\nM1006 A0 B10 L100 C0 D10 M100 E0 F10 N100\nM1006 A44 B10 L100 C0 D10 M100 E48 F10 N100\nM1006 A0 B10 L100 C0 D10 M100 E0 F10 N100\nM1006 A44 B20 L100 C41 D20 M100 E49 F20 N100\nM1006 A0 B20 L100 C0 D20 M100 E0 F20 N100\nM1006 A0 B20 L100 C37 D20 M100 E37 F20 N100\nM1006 W\n;=====printer finish  sound=========\nM400 S1\nM18 X Y Z\n
; machine_hotend_change_time = 0
; machine_load_filament_time = 28
; machine_max_acceleration_e = 5000,5000
; machine_max_acceleration_extruding = 20000,20000
; machine_max_acceleration_retracting = 5000,5000
; machine_max_acceleration_travel = 6000,6000
; machine_max_acceleration_x = 6000,6000
; machine_max_acceleration_y = 6000,6000
; machine_max_acceleration_z = 1500,1500
; machine_max_force_Y = 0
; machine_max_jerk_e = 3,3
; machine_max_jerk_x = 9,9
; machine_max_jerk_y = 9,9
; machine_max_jerk_z = 5,5
; machine_max_printed_mass = 0
; machine_max_speed_e = 30,30
; machine_max_speed_x = 500,200
; machine_max_speed_y = 500,200
; machine_max_speed_z = 30,30
; machine_min_extruding_rate = 0,0
; machine_min_travel_rate = 0,0
; machine_pause_gcode = M400 U1
; machine_prepare_compensation_time = 260
; machine_start_gcode = ;===== machine: A1 mini =========================\n;===== date: 20260513 ==================\n\n;===== start to heat heatbead&hotend==========\nM1002 gcode_claim_action : 2\nM1002 set_filament_type:{filament_type[initial_no_support_extruder]}\nM104 S170\nM140 S[bed_temperature_initial_layer_single]\nG392 S0 ;turn off clog detect\nM9833.2\n;=====start printer sound ===================\nM17\nM400 S1\nM1006 S1\nM1006 A0 B0 L100 C37 D10 M100 E37 F10 N100\nM1006 A0 B0 L100 C41 D10 M100 E41 F10 N100\nM1006 A0 B0 L100 C44 D10 M100 E44 F10 N100\nM1006 A0 B10 L100 C0 D10 M100 E0 F10 N100\nM1006 A43 B10 L100 C39 D10 M100 E46 F10 N100\nM1006 A0 B0 L100 C0 D10 M100 E0 F10 N100\nM1006 A0 B0 L100 C39 D10 M100 E43 F10 N100\nM1006 A0 B0 L100 C0 D10 M100 E0 F10 N100\nM1006 A0 B0 L100 C41 D10 M100 E41 F10 N100\nM1006 A0 B0 L100 C44 D10 M100 E44 F10 N100\nM1006 A0 B0 L100 C49 D10 M100 E49 F10 N100\nM1006 A0 B0 L100 C0 D10 M100 E0 F10 N100\nM1006 A44 B10 L100 C39 D10 M100 E48 F10 N100\nM1006 A0 B0 L100 C0 D10 M100 E0 F10 N100\nM1006 A0 B0 L100 C39 D10 M100 E44 F10 N100\nM1006 A0 B0 L100 C0 D10 M100 E0 F10 N100\nM1006 A43 B10 L100 C39 D10 M100 E46 F10 N100\nM1006 W\nM18\n;=====avoid end stop =================\nG91\nG380 S2 Z30 F1200\nG380 S3 Z-20 F1200\nG1 Z5 F1200\nG90\n\n;===== reset machine status =================\nM204 S6000\n\nM630 S0 P0\nG91\nM17 Z0.3 ; lower the z-motor current\n\nG90\nM17 X0.7 Y0.9 Z0.5 ; reset motor current to default\nM960 S5 P1 ; turn on logo lamp\nG90\nM83\nM220 S100 ;Reset Feedrate\nM221 S100 ;Reset Flowrate\nM73.2   R1.0 ;Reset left time magnitude\n;====== cog noise reduction=================\nM982.2 S1 ; turn on cog noise reduction\n\n;===== prepare print temperature and material ==========\nM400\nM18\nM109 S100 H170\nM104 S170\nM400\nM17\nM400\nG28 X\n\nM211 X0 Y0 Z0 ;turn off soft endstop ; turn off soft endstop to prevent protential logic problem\n\nM975 S1 ; turn on\n\nG1 X0.0 F30000\nG1 X-13.5 F3000\n\nM620 M ;enable remap\nM620 S[initial_no_support_extruder]A   ; switch material if AMS exist\n    G392 S0 ;turn on clog detect\n    M1002 gcode_claim_action : 4\n    M400\n    M1002 set_filament_type:UNKNOWN\n    M109 S[nozzle_temperature_initial_layer]\n{if (filament_type[initial_no_support_extruder] == \"PLA\") && (nozzle_diameter != 0.2)}\n    M104 S220\n{else}\n    M104 S250\n{endif}\n    M400\n    T[initial_no_support_extruder]\n    G1 X-13.5 F3000\n    M400\n{if (filament_type[initial_no_support_extruder] == \"PLA\") && (nozzle_diameter != 0.2)}\n    M620.1 E F{flush_volumetric_speeds[initial_no_support_extruder]/2.4053*60} T220\n    M109 S220 ;set nozzle to common flush temp\n{else}\n    M620.1 E F{flush_volumetric_speeds[initial_no_support_extruder]/2.4053*60} T{flush_temperatures[initial_no_support_extruder]}\n    M109 S250 ;set nozzle to common flush temp\n{endif}\n    M106 P1 S0\n    G92 E0\n    G1 E50 F200\n    M400\n    M1002 set_filament_type:{filament_type[initial_no_support_extruder]}\n{if (filament_type[initial_no_support_extruder] == \"PLA\") && (nozzle_diameter != 0.2)}\n    M104 S220\n{else}\n    M104 S{flush_temperatures[initial_no_support_extruder]}\n{endif}\n    G92 E0\n    G1 E50 F{flush_volumetric_speeds[initial_no_support_extruder]/2.4053*60}\n    M400\n    M106 P1 S178\n    G92 E0\n    G1 E5 F{flush_volumetric_speeds[initial_no_support_extruder]/2.4053*60}\n    M109 S{nozzle_temperature_initial_layer[initial_no_support_extruder]-20} ; drop nozzle temp, make filament shink a bit\n    M104 S{nozzle_temperature_initial_layer[initial_no_support_extruder]-40}\n    G92 E0\n    G1 E-0.5 F300\n\n    G1 X0 F30000\n    G1 X-13.5 F3000\n    G1 X0 F30000 ;wipe and shake\n    G1 X-13.5 F3000\n    G1 X0 F12000 ;wipe and shake\n    G1 X0 F30000\n    G1 X-13.5 F3000\n    M109 S{nozzle_temperature_initial_layer[initial_no_support_extruder]-40}\n    G392 S0 ;turn off clog detect\nM621 S[initial_no_support_extruder]A\n\nM400\nM106 P1 S0\n;===== prepare print temperature and material end =====\n\n\n;===== mech mode fast check============================\nM1002 gcode_claim_action : 3\nG0 X25 Y175 F20000 ; find a soft place to home\n;M104 S0\nG28 Z P0 T300; home z with low precision,permit 300deg temperature\nG29.2 S0 ; turn off ABL\nM104 S170\n\n; build plate detect\nM1002 judge_flag build_plate_detect_flag\nM622 S1\n  G39.4\n  M400\nM623\n\nG1 Z5 F3000\nG1 X90 Y-1 F30000\nM400 P200\nM970.3 Q1 A7 K0 O2\nM974 Q1 S2 P0\n\nG1 X90 Y0 Z5 F30000\nM400 P200\nM970 Q0 A10 B50 C90 H15 K0 M20 O3\nM974 Q0 S2 P0\n\nM975 S1\nG1 F30000\nG1 X-1 Y10\nG28 X ; re-home XY\n\n;===== wipe nozzle ===============================\nM1002 gcode_claim_action : 14\nM975 S1\n\nM104 S170 ; set temp down to heatbed acceptable\nM106 S255 ; turn on fan (G28 has turn off fan)\nM211 S; push soft endstop status\nM211 X0 Y0 Z0 ;turn off Z axis endstop\n\nM83\nG1 E-1 F500\nG90\nM83\n\nM109 S170\nM104 S140\nG0 X90 Y-4 F30000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X91 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X92 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X93 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X94 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X95 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X96 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X97 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X98 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X99 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X99 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X99 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X99 F10000\nG380 S3 Z-5 F1200\nG1 Z2 F1200\nG1 X99 F10000\nG380 S3 Z-5 F1200\n\nG1 Z5 F30000\n;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\nG1 X25 Y175 F30000.1 ;Brush material\nG1 Z0.2 F30000.1\nG1 Y185\nG91\nG1 X-30 F30000\nG1 Y-2\nG1 X27\nG1 Y1.5\nG1 X-28\nG1 Y-2\nG1 X30\nG1 Y1.5\nG1 X-30\nG90\nM83\n\nG1 Z5 F3000\nG0 X50 Y175 F20000 ; find a soft place to home\nG28 Z P0 T300; home z with low precision, permit 300deg temperature\nG29.2 S0 ; turn off ABL\n\nG0 X85 Y185 F10000 ;move to exposed steel surface and stop the nozzle\nG0 Z-1.01 F10000\nG91\n\nG2 I1 J0 X2 Y0 F2000.1\nG2 I-0.75 J0 X-1.5\nG2 I1 J0 X2\nG2 I-0.75 J0 X-1.5\nG2 I1 J0 X2\nG2 I-0.75 J0 X-1.5\nG2 I1 J0 X2\nG2 I-0.75 J0 X-1.5\nG2 I1 J0 X2\nG2 I-0.75 J0 X-1.5\nG2 I1 J0 X2\nG2 I-0.75 J0 X-1.5\nG2 I1 J0 X2\nG2 I-0.75 J0 X-1.5\nG2 I1 J0 X2\nG2 I-0.75 J0 X-1.5\nG2 I1 J0 X2\nG2 I-0.75 J0 X-1.5\nG2 I1 J0 X2\nG2 I-0.75 J0 X-1.5\n\nG90\nG1 Z5 F30000\nG1 X25 Y175 F30000.1 ;Brush material\nG1 Z0.2 F30000.1\nG1 Y185\nG91\nG1 X-30 F30000\nG1 Y-2\nG1 X27\nG1 Y1.5\nG1 X-28\nG1 Y-2\nG1 X30\nG1 Y1.5\nG1 X-30\nG90\nM83\n\nG1 Z5\nG0 X55 Y175 F20000 ; find a soft place to home\nG28 Z P0 T300; home z with low precision, permit 300deg temperature\nG29.2 S0 ; turn off ABL\n\nG1 Z10\nG1 X85 Y185\nG1 Z-1.01\nG1 X95\nG1 X90\n\nM211 R; pop softend status\n\nM106 S0 ; turn off fan , too noisy\n;===== wipe nozzle end ================================\n\n\n;===== wait heatbed  ====================\nM1002 gcode_claim_action:54\nM104 S0\nM190 S[bed_temperature_initial_layer_single];set bed temp\nM109 S140\n\nG1 Z5 F3000\nG29.2 S1\nG1 X10 Y10 F20000\n\n;===== bed leveling ==================================\n;M1002 set_flag g29_before_print_flag=1\nM1002 judge_flag g29_before_print_flag\nM622 J1\n    M1002 gcode_claim_action : 1\n    G29 A1 X{first_layer_print_min[0]} Y{first_layer_print_min[1]} I{first_layer_print_size[0]} J{first_layer_print_size[1]}\n    M400\n    M500 ; save cali data\nM623\n;===== bed leveling end ================================\n\n;===== home after wipe mouth============================\nM1002 judge_flag g29_before_print_flag\nM622 J0\n\n    M1002 gcode_claim_action : 13\n    G28 T145\n\nM623\n\n;===== home after wipe mouth end =======================\n\nM975 S1 ; turn on vibration supression\n;===== nozzle load line ===============================\nM975 S1\nG90\nM83\nT1000\n\nG1 X-13.5 Y0 Z10 F10000\nG1 E1.2 F500\nM400\nM1002 set_filament_type:UNKNOWN\nM109 S{nozzle_temperature[initial_extruder]}\nM400\n\nM412 S1 ;    ===turn on  filament runout detection===\nM400 P10\n\nG392 S0 ;turn on clog detect\n\nM620.3 W1; === turn on filament tangle detection===\nM400 S2\n\nM1002 set_filament_type:{filament_type[initial_no_support_extruder]}\n;M1002 set_flag extrude_cali_flag=1\nM1002 judge_flag extrude_cali_flag\nM622 J1\n    M1002 gcode_claim_action : 8\n    \n    M400\n    M900 K0.0 L1000.0 M1.0\n    G90\n    M83\n    G0 X68 Y-4 F30000\n    G0 Z0.3 F18000 ;Move to start position\n    M400\n    G0 X88 E10  F{outer_wall_volumetric_speed/(24/20)    * 60}\n    G0 X93 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)/4     * 60}\n    G0 X98 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)     * 60}\n    G0 X103 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)/4     * 60}\n    G0 X108 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)     * 60}\n    G0 X113 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)/4     * 60}\n    G0 Y0 Z0 F20000\n    M400\n    \n    G1 X-13.5 Y0 Z10 F10000\n    M400\n    \n    G1 E10 F{outer_wall_volumetric_speed/2.4*60}\n    M983 F{outer_wall_volumetric_speed/2.4} A0.3 H[nozzle_diameter]; cali dynamic extrusion compensation\n    M106 P1 S178\n    M400 S7\n    G1 X0 F18000\n    G1 X-13.5 F3000\n    G1 X0 F18000 ;wipe and shake\n    G1 X-13.5 F3000\n    G1 X0 F12000 ;wipe and shake\n    G1 X-13.5 F3000\n    M400\n    M106 P1 S0\n\n    M1002 judge_last_extrude_cali_success\n    M622 J0\n        M983 F{outer_wall_volumetric_speed/2.4} A0.3 H[nozzle_diameter]; cali dynamic extrusion compensation\n        M106 P1 S178\n        M400 S7\n        G1 X0 F18000\n        G1 X-13.5 F3000\n        G1 X0 F18000 ;wipe and shake\n        G1 X-13.5 F3000\n        G1 X0 F12000 ;wipe and shake\n        M400\n        M106 P1 S0\n    M623\n    \n    G1 X-13.5 F3000\n    M400\n    M984 A0.1 E1 S1 F{outer_wall_volumetric_speed/2.4} H[nozzle_diameter]\n    M106 P1 S178\n    M400 S7\n    G1 X0 F18000\n    G1 X-13.5 F3000\n    G1 X0 F18000 ;wipe and shake\n    G1 X-13.5 F3000\n    G1 X0 F12000 ;wipe and shake\n    G1 X-13.5 F3000\n    M400\n    M106 P1 S0\n\nM623 ; end of \"draw extrinsic para cali paint\"\n\n;===== extrude cali test ===============================\nM104 S{nozzle_temperature_initial_layer[initial_extruder]}\nG90\nM83\nG0 X68 Y-2.5 F30000\nG0 Z0.3 F18000 ;Move to start position\nG0 X88 E10  F{outer_wall_volumetric_speed/(24/20)    * 60}\nG0 X93 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)/4     * 60}\nG0 X98 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)     * 60}\nG0 X103 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)/4     * 60}\nG0 X108 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)     * 60}\nG0 X113 E.3742  F{outer_wall_volumetric_speed/(0.3*0.5)/4     * 60}\nG0 X115 Z0 F20000\nG0 Z5\nM400\n\n;========turn off light and wait extrude temperature =============\nM1002 gcode_claim_action : 0\n\nM400 ; wait all motion done before implement the emprical L parameters\n\n;===== for Textured PEI Plate , lower the nozzle as the nozzle was touching topmost of the texture when homing ==\n;curr_bed_type={curr_bed_type}\n{if curr_bed_type==\"Textured PEI Plate\"}\nG29.1 Z{-0.02} ; for Textured PEI Plate\n{endif}\n\nM960 S1 P0 ; turn off laser\nM960 S2 P0 ; turn off laser\nM106 S0 ; turn off fan\nM106 P2 S0 ; turn off big fan\nM106 P3 S0 ; turn off chamber fan\n\nM975 S1 ; turn on mech mode supression\nG90\nM83\nT1000\n\nM211 X0 Y0 Z0 ;turn off soft endstop\nM1007 S1\n\n\n\n
; machine_switch_extruder_time = 0
; machine_unload_filament_time = 34
; master_extruder_id = 1
; max_bridge_length = 0
; max_layer_height = 0.28
; max_travel_detour_distance = 0
; min_bead_width = 85%
; min_feature_size = 25%
; min_layer_height = 0.08
; minimum_sparse_infill_area = 15
; mmu_segmented_region_interlocking_depth = 0
; mmu_segmented_region_max_width = 0
; monotonic_travel_into_wall = 0%
; no_slow_down_for_cooling_on_outwalls = 0
; nozzle_diameter = 0.4
; nozzle_flush_dataset = 0
; nozzle_height = 4.76
; nozzle_temperature = 220
; nozzle_temperature_initial_layer = 220
; nozzle_temperature_range_high = 240
; nozzle_temperature_range_low = 190
; nozzle_type = stainless_steel
; nozzle_volume = 92
; nozzle_volume_type = Standard
; only_one_wall_first_layer = 0
; ooze_prevention = 0
; other_layers_print_sequence = 0
; other_layers_print_sequence_nums = 0
; outer_wall_acceleration = 5000
; outer_wall_jerk = 9
; outer_wall_line_width = 0.42
; outer_wall_speed = 60
; overhang_1_4_speed = 0
; overhang_2_4_speed = 50
; overhang_3_4_speed = 30
; overhang_4_4_speed = 10
; overhang_fan_speed = 100
; overhang_fan_threshold = 50%
; overhang_threshold_participating_cooling = 95%
; overhang_totally_speed = 10
; override_filament_scarf_seam_setting = 0
; override_process_overhang_speed = 0
; physical_extruder_map = 0
; post_process = 
; pre_start_fan_time = 0
; precise_outer_wall = 0
; precise_z_height = 0
; pressure_advance = 0.02
; prime_tower_brim_width = 3
; prime_tower_enable_framework = 0
; prime_tower_extra_rib_length = 0
; prime_tower_fillet_wall = 1
; prime_tower_flat_ironing = 0
; prime_tower_infill_gap = 150%
; prime_tower_lift_height = -1
; prime_tower_lift_speed = 90
; prime_tower_max_speed = 90
; prime_tower_rib_wall = 1
; prime_tower_rib_width = 8
; prime_tower_skip_points = 1
; prime_tower_width = 35
; prime_volume_mode = Default
; print_compatible_printers = "Bambu Lab A1 mini 0.4 nozzle"
; print_extruder_id = 1
; print_extruder_variant = "Direct Drive Standard"
; print_flow_ratio = 1
; print_in_clockwise = 0
; print_sequence = by layer
; print_settings_id = 0.20mm Strength @BBL A1M
; printable_area = 0x0,180x0,180x180,0x180
; printable_height = 180
; printer_extruder_id = 1
; printer_extruder_variant = "Direct Drive Standard"
; printer_model = Bambu Lab A1 mini
; printer_notes = 
; printer_settings_id = Bambu Lab A1 mini 0.4 nozzle
; printer_structure = i3
; printer_technology = FFF
; printer_variant = 0.4
; printing_by_object_gcode = 
; process_notes = 
; raft_contact_distance = 0.1
; raft_expansion = 1.5
; raft_first_layer_density = 90%
; raft_first_layer_expansion = -1
; raft_layers = 0
; reduce_crossing_wall = 0
; reduce_fan_stop_start_freq = 1
; reduce_infill_retraction_mode = Auto
; required_nozzle_HRC = 3
; resolution = 0.012
; retract_before_wipe = 0%
; retract_length_toolchange = 2
; retract_lift_above = 0
; retract_lift_below = 179
; retract_restart_extra = 0
; retract_restart_extra_toolchange = 0
; retract_when_changing_layer = 1
; retraction_distances_when_cut = 18
; retraction_distances_when_ec = 0
; retraction_length = 0.8
; retraction_minimum_travel = 1
; retraction_speed = 30
; role_base_wipe_speed = 1
; scan_first_layer = 0
; scarf_angle_threshold = 155
; seam_gap = 15%
; seam_placement_away_from_overhangs = 0
; seam_position = aligned
; seam_slope_conditional = 1
; seam_slope_entire_loop = 0
; seam_slope_gap = 0
; seam_slope_inner_walls = 1
; seam_slope_min_length = 10
; seam_slope_start_height = 10%
; seam_slope_steps = 10
; seam_slope_type = none
; silent_mode = 0
; single_extruder_multi_material = 1
; skeleton_infill_density = 25%
; skeleton_infill_line_width = 0.45
; skin_infill_density = 25%
; skin_infill_depth = 2
; skin_infill_line_width = 0.45
; skirt_distance = 2
; skirt_height = 1
; skirt_loops = 0
; skirt_per_object = 1
; slice_closing_radius = 0.049
; slicing_mode = regular
; slow_down_for_layer_cooling = 1
; slow_down_layer_time = 8
; slow_down_min_speed = 20
; slowdown_end_acc = 100000
; slowdown_end_height = 400
; slowdown_end_speed = 1000
; slowdown_start_acc = 100000
; slowdown_start_height = 0
; slowdown_start_speed = 1000
; small_perimeter_speed = 50%
; small_perimeter_threshold = 0
; smooth_coefficient = 80
; smooth_speed_discontinuity_area = 1
; solid_infill_filament = 0
; sparse_infill_acceleration = 100%
; sparse_infill_anchor = 400%
; sparse_infill_anchor_max = 20
; sparse_infill_density = 25%
; sparse_infill_filament = 0
; sparse_infill_lattice_angle_1 = -45
; sparse_infill_lattice_angle_2 = 45
; sparse_infill_line_width = 0.45
; sparse_infill_pattern = gyroid
; sparse_infill_speed = 270
; spiral_mode = 0
; spiral_mode_max_xy_smoothing = 200%
; spiral_mode_smooth = 0
; standby_temperature_delta = -5
; start_end_points = 30x-3,54x245
; supertack_plate_temp = 45
; supertack_plate_temp_initial_layer = 45
; support_air_filtration = 0
; support_angle = 0
; support_base_pattern = default
; support_base_pattern_spacing = 2.5
; support_bottom_interface_spacing = 0.5
; support_bottom_z_distance = 0.2
; support_chamber_temp_control = 0
; support_cooling_filter = 0
; support_critical_regions_only = 0
; support_expansion = 0
; support_fast_purge_mode = 0
; support_filament = 0
; support_interface_bottom_layers = 2
; support_interface_filament = 0
; support_interface_loop_pattern = 0
; support_interface_not_for_body = 1
; support_interface_pattern = auto
; support_interface_spacing = 0.5
; support_interface_speed = 80
; support_interface_top_layers = 2
; support_ironing_direction = 0
; support_ironing_flow = 10%
; support_ironing_inset = 0
; support_ironing_pattern = zig-zag
; support_ironing_spacing = 0.15
; support_ironing_speed = 30
; support_line_width = 0.42
; support_object_first_layer_gap = 0.2
; support_object_skip_flush = 0
; support_object_xy_distance = 0.35
; support_on_build_plate_only = 1
; support_remove_small_overhang = 1
; support_speed = 150
; support_style = default
; support_threshold_angle = 40
; support_top_z_distance = 0.2
; support_type = tree(auto)
; symmetric_infill_y_axis = 0
; temperature_vitrification = 45
; template_custom_gcode = 
; textured_plate_temp = 65
; textured_plate_temp_initial_layer = 65
; thick_bridges = 0
; thumbnail_size = 50x50
; time_lapse_gcode = ;===================== date: 20250206 =====================\n{if !spiral_mode && print_sequence != \"by object\"}\n; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer\n; SKIPPABLE_START\n; SKIPTYPE: timelapse\nM622.1 S1 ; for prev firmware, default turned on\nM1002 judge_flag timelapse_record_flag\nM622 J1\nG92 E0\nG1 Z{max_layer_z + 0.4}\nG1 X0 Y{first_layer_center_no_wipe_tower[1]} F18000 ; move to safe pos\nG1 X-13.0 F3000 ; move to safe pos\nM400\nM1004 S5 P1  ; external shutter\nM400 P300\nM971 S11 C11 O0\nG92 E0\nG1 X0 F18000\nM623\n\n; SKIPTYPE: head_wrap_detect\nM622.1 S1\nM1002 judge_flag g39_3rd_layer_detect_flag\nM622 J1\n    ; enable nozzle clog detect at 3rd layer\n    {if layer_num == 2}\n      M400\n      G90\n      M83\n      M204 S5000\n      G0 Z2 F4000\n      G0 X187 Y178 F20000\n      G39 S1 X187 Y178\n      G0 Z2 F4000\n    {endif}\n\n\n    M622.1 S1\n    M1002 judge_flag g39_detection_flag\n    M622 J1\n      {if !in_head_wrap_detect_zone}\n        M622.1 S0\n        M1002 judge_flag g39_mass_exceed_flag\n        M622 J1\n        {if layer_num > 2}\n            G392 S0\n            M400\n            G90\n            M83\n            M204 S5000\n            G0 Z{max_layer_z + 0.4} F4000\n            G39.3 S1\n            G0 Z{max_layer_z + 0.4} F4000\n            G392 S0\n          {endif}\n        M623\n    {endif}\n    M623\nM623\n; SKIPPABLE_END\n{endif}\n\n\n
; timelapse_type = 0
; top_area_threshold = 200%
; top_color_penetration_layers = 5
; top_one_wall_type = all top
; top_shell_layers = 6
; top_shell_thickness = 1
; top_solid_infill_flow_ratio = 1
; top_surface_acceleration = 2000
; top_surface_density = 100%
; top_surface_jerk = 9
; top_surface_line_width = 0.42
; top_surface_pattern = monotonicline
; top_surface_speed = 200
; top_z_overrides_xy_distance = 0
; travel_acceleration = 10000
; travel_jerk = 9
; travel_short_distance_acceleration = 250
; travel_speed = 700
; travel_speed_z = 0
; tree_support_branch_angle = 45
; tree_support_branch_diameter = 2
; tree_support_branch_diameter_angle = 5
; tree_support_branch_distance = 5
; tree_support_wall_count = -1
; upward_compatible_machine = "Bambu Lab P1S 0.4 nozzle";"Bambu Lab P1P 0.4 nozzle";"Bambu Lab X1 0.4 nozzle";"Bambu Lab X1 Carbon 0.4 nozzle";"Bambu Lab X1E 0.4 nozzle";"Bambu Lab A1 0.4 nozzle";"Bambu Lab H2D 0.4 nozzle";"Bambu Lab H2D Pro 0.4 nozzle";"Bambu Lab H2S 0.4 nozzle";"Bambu Lab P2S 0.4 nozzle";"Bambu Lab H2C 0.4 nozzle";"Bambu Lab X2D 0.4 nozzle";"Bambu Lab A2L 0.4 nozzle"
; use_firmware_retraction = 0
; use_relative_e_distances = 1
; vertical_shell_speed = 80%
; volumetric_speed_coefficients = "0 0 0 0 0 0"
; wall_distribution_count = 1
; wall_filament = 0
; wall_generator = classic
; wall_loops = 6
; wall_sequence = inner wall/outer wall
; wall_transition_angle = 10
; wall_transition_filter_deviation = 25%
; wall_transition_length = 100%
; wipe = 1
; wipe_distance = 2
; wipe_speed = 80%
; wipe_tower_no_sparse_layers = 0
; wipe_tower_rotation_angle = 0
; wipe_tower_x = 15
; wipe_tower_y = 220
; wrapping_detection_gcode = 
; wrapping_detection_layers = 20
; wrapping_exclude_area = 
; xy_contour_compensation = 0
; xy_hole_compensation = 0
; z_direction_outwall_speed_continuous = 0
; z_hop = 0.4
; z_hop_types = Auto Lift
; CONFIG_BLOCK_END

; EXECUTABLE_BLOCK_START
M73 P0 R24
M201 X6000 Y6000 Z1500 E5000
M203 X500 Y500 Z30 E30
M204 P20000 R5000 T20000
M205 X9.00 Y9.00 Z5.00 E3.00
M106 S0
; FEATURE: Custom
;===== machine: A1 mini =========================
;===== date: 20260513 ==================

;===== start to heat heatbead&hotend==========
M1002 gcode_claim_action : 2
M1002 set_filament_type:PLA
M104 S170
M140 S65
G392 S0 ;turn off clog detect
M9833.2
;=====start printer sound ===================
M17
M400 S1
M1006 S1
M1006 A0 B0 L100 C37 D10 M100 E37 F10 N100
M1006 A0 B0 L100 C41 D10 M100 E41 F10 N100
M1006 A0 B0 L100 C44 D10 M100 E44 F10 N100
M1006 A0 B10 L100 C0 D10 M100 E0 F10 N100
M1006 A43 B10 L100 C39 D10 M100 E46 F10 N100
M1006 A0 B0 L100 C0 D10 M100 E0 F10 N100
M1006 A0 B0 L100 C39 D10 M100 E43 F10 N100
M1006 A0 B0 L100 C0 D10 M100 E0 F10 N100
M1006 A0 B0 L100 C41 D10 M100 E41 F10 N100
M1006 A0 B0 L100 C44 D10 M100 E44 F10 N100
M1006 A0 B0 L100 C49 D10 M100 E49 F10 N100
M1006 A0 B0 L100 C0 D10 M100 E0 F10 N100
M1006 A44 B10 L100 C39 D10 M100 E48 F10 N100
M1006 A0 B0 L100 C0 D10 M100 E0 F10 N100
M1006 A0 B0 L100 C39 D10 M100 E44 F10 N100
M1006 A0 B0 L100 C0 D10 M100 E0 F10 N100
M1006 A43 B10 L100 C39 D10 M100 E46 F10 N100
M1006 W
M18
;=====avoid end stop =================
G91
G380 S2 Z30 F1200
G380 S3 Z-20 F1200
G1 Z5 F1200
G90

;===== reset machine status =================
M204 S6000

M630 S0 P0
G91
M17 Z0.3 ; lower the z-motor current

G90
M17 X0.7 Y0.9 Z0.5 ; reset motor current to default
M960 S5 P1 ; turn on logo lamp
G90
M83
M220 S100 ;Reset Feedrate
M221 S100 ;Reset Flowrate
M73.2   R1.0 ;Reset left time magnitude
;====== cog noise reduction=================
M982.2 S1 ; turn on cog noise reduction

;===== prepare print temperature and material ==========
M400
M18
M109 S100 H170
M104 S170
M400
M17
M400
G28 X

M211 X0 Y0 Z0 ;turn off soft endstop ; turn off soft endstop to prevent protential logic problem

M975 S1 ; turn on

G1 X0.0 F30000
G1 X-13.5 F3000

M620 M ;enable remap
M620 S0A   ; switch material if AMS exist
    G392 S0 ;turn on clog detect
    M1002 gcode_claim_action : 4
    M400
    M1002 set_filament_type:UNKNOWN
    M109 S220

    M104 S220

    M400
    T0
    G1 X-13.5 F3000
    M400

    M620.1 E F299.339 T220
    M109 S220 ;set nozzle to common flush temp

    M106 P1 S0
    G92 E0
M73 P1 R24
    G1 E50 F200
    M400
    M1002 set_filament_type:PLA

    M104 S220

    G92 E0
    G1 E50 F299.339
    M400
    M106 P1 S178
    G92 E0
M73 P3 R24
    G1 E5 F299.339
    M109 S200 ; drop nozzle temp, make filament shink a bit
    M104 S180
    G92 E0
M73 P3 R23
    G1 E-0.5 F300

    G1 X0 F30000
    G1 X-13.5 F3000
    G1 X0 F30000 ;wipe and shake
    G1 X-13.5 F3000
    G1 X0 F12000 ;wipe and shake
    G1 X0 F30000
    G1 X-13.5 F3000
    M109 S180
    G392 S0 ;turn off clog detect
M621 S0A

M400
M106 P1 S0
;===== prepare print temperature and material end =====


;===== mech mode fast check============================
M1002 gcode_claim_action : 3
G0 X25 Y175 F20000 ; find a soft place to home
;M104 S0
G28 Z P0 T300; home z with low precision,permit 300deg temperature
G29.2 S0 ; turn off ABL
M104 S170

; build plate detect
M1002 judge_flag build_plate_detect_flag
M622 S1
  G39.4
  M400
M623

G1 Z5 F3000
G1 X90 Y-1 F30000
M400 P200
M970.3 Q1 A7 K0 O2
M974 Q1 S2 P0

G1 X90 Y0 Z5 F30000
M400 P200
M970 Q0 A10 B50 C90 H15 K0 M20 O3
M974 Q0 S2 P0

M975 S1
G1 F30000
G1 X-1 Y10
G28 X ; re-home XY

;===== wipe nozzle ===============================
M1002 gcode_claim_action : 14
M975 S1

M104 S170 ; set temp down to heatbed acceptable
M106 S255 ; turn on fan (G28 has turn off fan)
M211 S; push soft endstop status
M211 X0 Y0 Z0 ;turn off Z axis endstop

M83
G1 E-1 F500
G90
M83

M109 S170
M104 S140
G0 X90 Y-4 F30000
G380 S3 Z-5 F1200
M73 P21 R19
G1 Z2 F1200
G1 X91 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X92 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X93 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X94 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X95 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X96 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X97 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X98 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X99 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X99 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X99 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X99 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X99 F10000
G380 S3 Z-5 F1200

G1 Z5 F30000
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
G1 X25 Y175 F30000.1 ;Brush material
G1 Z0.2 F30000.1
G1 Y185
G91
G1 X-30 F30000
G1 Y-2
G1 X27
G1 Y1.5
G1 X-28
G1 Y-2
G1 X30
G1 Y1.5
G1 X-30
G90
M83

G1 Z5 F3000
G0 X50 Y175 F20000 ; find a soft place to home
G28 Z P0 T300; home z with low precision, permit 300deg temperature
G29.2 S0 ; turn off ABL

G0 X85 Y185 F10000 ;move to exposed steel surface and stop the nozzle
G0 Z-1.01 F10000
G91

G2 I1 J0 X2 Y0 F2000.1
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5

G90
G1 Z5 F30000
G1 X25 Y175 F30000.1 ;Brush material
G1 Z0.2 F30000.1
G1 Y185
G91
G1 X-30 F30000
G1 Y-2
G1 X27
G1 Y1.5
G1 X-28
G1 Y-2
G1 X30
G1 Y1.5
G1 X-30
G90
M83

G1 Z5
G0 X55 Y175 F20000 ; find a soft place to home
G28 Z P0 T300; home z with low precision, permit 300deg temperature
G29.2 S0 ; turn off ABL

G1 Z10
G1 X85 Y185
G1 Z-1.01
G1 X95
G1 X90

M211 R; pop softend status

M106 S0 ; turn off fan , too noisy
;===== wipe nozzle end ================================


;===== wait heatbed  ====================
M1002 gcode_claim_action:54
M104 S0
M190 S65;set bed temp
M109 S140

G1 Z5 F3000
G29.2 S1
G1 X10 Y10 F20000

;===== bed leveling ==================================
;M1002 set_flag g29_before_print_flag=1
M1002 judge_flag g29_before_print_flag
M622 J1
    M1002 gcode_claim_action : 1
    G29 A1 X54.8543 Y53.0793 I68.5603 J73.8414
    M400
    M500 ; save cali data
M623
;===== bed leveling end ================================

;===== home after wipe mouth============================
M1002 judge_flag g29_before_print_flag
M622 J0

    M1002 gcode_claim_action : 13
    G28 T145

M623

;===== home after wipe mouth end =======================

M975 S1 ; turn on vibration supression
;===== nozzle load line ===============================
M975 S1
G90
M83
T1000

G1 X-13.5 Y0 Z10 F10000
G1 E1.2 F500
M400
M1002 set_filament_type:UNKNOWN
M109 S220
M400

M412 S1 ;    ===turn on  filament runout detection===
M400 P10

G392 S0 ;turn on clog detect

M620.3 W1; === turn on filament tangle detection===
M400 S2

M1002 set_filament_type:PLA
;M1002 set_flag extrude_cali_flag=1
M1002 judge_flag extrude_cali_flag
M622 J1
    M1002 gcode_claim_action : 8
    
    M400
    M900 K0.0 L1000.0 M1.0
    G90
    M83
    G0 X68 Y-4 F30000
    G0 Z0.3 F18000 ;Move to start position
    M400
    G0 X88 E10  F271.497
    G0 X93 E.3742  F452.496
    G0 X98 E.3742  F1809.98
    G0 X103 E.3742  F452.496
    G0 X108 E.3742  F1809.98
    G0 X113 E.3742  F452.496
    G0 Y0 Z0 F20000
    M400
    
    G1 X-13.5 Y0 Z10 F10000
    M400
    
    G1 E10 F113.124
    M983 F1.8854 A0.3 H0.4; cali dynamic extrusion compensation
    M106 P1 S178
    M400 S7
    G1 X0 F18000
    G1 X-13.5 F3000
    G1 X0 F18000 ;wipe and shake
    G1 X-13.5 F3000
    G1 X0 F12000 ;wipe and shake
    G1 X-13.5 F3000
    M400
    M106 P1 S0

    M1002 judge_last_extrude_cali_success
    M622 J0
        M983 F1.8854 A0.3 H0.4; cali dynamic extrusion compensation
        M106 P1 S178
        M400 S7
        G1 X0 F18000
        G1 X-13.5 F3000
        G1 X0 F18000 ;wipe and shake
M73 P22 R19
        G1 X-13.5 F3000
        G1 X0 F12000 ;wipe and shake
        M400
        M106 P1 S0
    M623
    
    G1 X-13.5 F3000
    M400
    M984 A0.1 E1 S1 F1.8854 H0.4
    M106 P1 S178
    M400 S7
    G1 X0 F18000
    G1 X-13.5 F3000
M73 P23 R19
    G1 X0 F18000 ;wipe and shake
    G1 X-13.5 F3000
    G1 X0 F12000 ;wipe and shake
    G1 X-13.5 F3000
    M400
    M106 P1 S0

M623 ; end of "draw extrinsic para cali paint"

;===== extrude cali test ===============================
M104 S220
G90
M83
G0 X68 Y-2.5 F30000
G0 Z0.3 F18000 ;Move to start position
G0 X88 E10  F271.497
G0 X93 E.3742  F452.496
G0 X98 E.3742  F1809.98
G0 X103 E.3742  F452.496
G0 X108 E.3742  F1809.98
G0 X113 E.3742  F452.496
G0 X115 Z0 F20000
G0 Z5
M400

;========turn off light and wait extrude temperature =============
M1002 gcode_claim_action : 0

M400 ; wait all motion done before implement the emprical L parameters

;===== for Textured PEI Plate , lower the nozzle as the nozzle was touching topmost of the texture when homing ==
;curr_bed_type=Textured PEI Plate

G29.1 Z-0.02 ; for Textured PEI Plate


M960 S1 P0 ; turn off laser
M960 S2 P0 ; turn off laser
M106 S0 ; turn off fan
M106 P2 S0 ; turn off big fan
M106 P3 S0 ; turn off chamber fan

M975 S1 ; turn on mech mode supression
G90
M83
T1000

M211 X0 Y0 Z0 ;turn off soft endstop
M1007 S1



; MACHINE_START_GCODE_END
; filament start gcode
M106 P3 S255
;Prevent PLA from jamming


;VT0 H-1
G90
G21
M83 ; use relative distances for extrusion
M981 S1 P20000 ;open spaghetti detector
; CHANGE_LAYER
; Z_HEIGHT: 0.2
; LAYER_HEIGHT: 0.2
G1 E-.8 F1800
; layer num/total_layer_count: 1/79
; update layer progress
M73 L1
M991 S0 P0 ;notify layer change
M106 S0
; OBJECT_ID: 105
G1 X55.131 Y57.11 F42000
M204 S6000
G1 Z.4
G1 Z.2
M73 P24 R18
G1 E.8 F1800
; FEATURE: Brim
; LINE_WIDTH: 0.5
G1 F3000
M204 S500
G1 X55.271 Y56.487 E.02377
G1 X55.628 Y55.644 E.0341
G1 X56.025 Y55.026 E.02737
G1 X56.451 Y54.547 E.02386
G1 X56.944 Y54.136 E.0239
G1 X57.489 Y53.803 E.0238
G1 X58.275 Y53.492 E.03148
G1 X58.955 Y53.346 E.02589
G1 X59.533 Y53.308 E.02157
G1 X118.717 Y53.308 E2.20438
G1 X119.365 Y53.356 E.02422
G1 X119.988 Y53.496 E.02377
G1 X120.831 Y53.853 E.0341
G1 X121.449 Y54.25 E.02737
G1 X121.928 Y54.676 E.02386
G1 X122.339 Y55.169 E.0239
G1 X122.672 Y55.714 E.02378
G1 X122.998 Y56.552 E.03351
M73 P25 R18
G1 X123.129 Y57.179 E.02386
G1 X123.167 Y57.758 E.0216
G1 X123.167 Y102.617 E1.67082
G1 X123.185 Y102.876 E.00967
G1 X123.186 Y122.183 E.71912
G1 X123.125 Y122.913 E.02728
G1 X122.961 Y123.587 E.02583
G1 X122.697 Y124.236 E.02612
G1 X122.366 Y124.786 E.02388
G1 X121.961 Y125.279 E.02378
G1 X121.268 Y125.869 E.03389
G1 X120.722 Y126.205 E.02388
G1 X120.132 Y126.457 E.0239
G1 X119.513 Y126.619 E.02383
G1 X118.715 Y126.692 E.02987
G1 X108.984 Y126.692 E.36244
G1 X108.335 Y126.644 E.02422
G1 X107.712 Y126.504 E.02377
G1 X106.869 Y126.147 E.0341
G1 X106.251 Y125.75 E.02737
G1 X105.772 Y125.324 E.02386
G1 X105.361 Y124.831 E.0239
G1 X105.028 Y124.286 E.02378
G1 X104.702 Y123.448 E.03351
G1 X104.571 Y122.821 E.02386
G1 X104.533 Y122.242 E.02159
G1 X104.533 Y115.421 E.25409
G1 X104.484 Y115.28 E.00555
G1 X104.304 Y115.192 E.00745
G1 X92.984 Y115.192 E.42166
G1 X92.335 Y115.144 E.02422
G1 X91.714 Y115.004 E.02373
G1 X90.787 Y114.601 E.03765
G1 X90.252 Y114.251 E.02381
G1 X89.772 Y113.824 E.0239
G1 X89.361 Y113.331 E.0239
G1 X89.028 Y112.786 E.0238
G1 X88.717 Y112 E.03148
G1 X88.571 Y111.32 E.02589
G1 X88.533 Y110.742 E.02157
G1 X88.533 Y100.758 E.37187
G1 X88.581 Y100.11 E.02422
G1 X88.721 Y99.489 E.02373
G1 X89.124 Y98.561 E.03767
G1 X89.475 Y98.026 E.02381
G1 X89.901 Y97.547 E.0239
G1 X90.394 Y97.136 E.0239
G1 X90.94 Y96.803 E.0238
G1 X91.725 Y96.492 E.03146
G1 X92.404 Y96.346 E.02589
G1 X92.983 Y96.308 E.02158
G1 X111.054 Y96.308 E.6731
G1 X111.195 Y96.259 E.00555
G1 X111.283 Y96.079 E.00745
G1 X111.283 Y67.421 E1.06742
G1 X111.234 Y67.28 E.00555
G1 X111.054 Y67.192 E.00745
G1 X67.196 Y67.192 E1.63357
G1 X67.055 Y67.241 E.00555
G1 X66.967 Y67.421 E.00745
G1 X66.967 Y94.741 E1.0176
G1 X66.919 Y95.39 E.02422
G1 X66.779 Y96.011 E.02373
G1 X66.376 Y96.939 E.03767
G1 X66.025 Y97.474 E.02381
G1 X65.599 Y97.953 E.0239
G1 X65.106 Y98.364 E.0239
G1 X64.56 Y98.697 E.0238
G1 X63.775 Y99.008 E.03146
G1 X63.096 Y99.154 E.02589
G1 X62.517 Y99.192 E.02158
G1 X59.534 Y99.192 E.11113
G1 X58.885 Y99.144 E.02422
G1 X58.262 Y99.004 E.02377
G1 X57.419 Y98.647 E.0341
G1 X56.801 Y98.25 E.02737
G1 X56.322 Y97.824 E.02386
G1 X55.911 Y97.331 E.0239
G1 X55.578 Y96.786 E.0238
G1 X55.267 Y96 E.03148
G1 X55.121 Y95.32 E.02589
G1 X55.083 Y94.742 E.02157
G1 X55.083 Y57.758 E1.37752
G1 X55.126 Y57.17 E.02198
M204 S6000
G1 X55.582 Y57.203 F42000
G1 F3000
M204 S500
G1 X55.583 Y57.188 E.00058
G1 X55.706 Y56.64 E.0209
G1 X56.03 Y55.869 E.03115
G1 X56.398 Y55.295 E.02541
G1 X56.778 Y54.87 E.02123
G1 X57.219 Y54.503 E.02137
G1 X57.705 Y54.209 E.02114
G1 X58.398 Y53.935 E.02775
G1 X59.008 Y53.802 E.02329
G1 X59.552 Y53.765 E.02031
G1 X118.705 Y53.765 E2.2032
G1 X119.287 Y53.808 E.02176
G1 X119.835 Y53.931 E.0209
G1 X120.606 Y54.255 E.03115
G1 X121.163 Y54.61 E.02461
G1 X121.591 Y54.988 E.02128
G1 X121.972 Y55.444 E.02213
G1 X122.265 Y55.928 E.02108
G1 X122.56 Y56.694 E.03056
G1 X122.673 Y57.232 E.02048
G1 X122.71 Y57.777 E.02037
G1 X122.71 Y102.612 E1.66993
G1 X122.728 Y102.896 E.0106
G1 X122.729 Y122.158 E.71744
G1 X122.67 Y122.85 E.02584
G1 X122.521 Y123.455 E.02322
G1 X122.281 Y124.04 E.02356
G1 X121.997 Y124.513 E.02053
G1 X121.641 Y124.947 E.02094
G1 X120.989 Y125.504 E.03191
G1 X120.502 Y125.802 E.02129
G1 X119.974 Y126.026 E.02137
G1 X119.423 Y126.169 E.0212
G1 X118.687 Y126.235 E.0275
G1 X108.995 Y126.235 E.36099
G1 X108.413 Y126.192 E.02176
G1 X107.865 Y126.07 E.0209
G1 X107.094 Y125.745 E.03115
G1 X106.52 Y125.377 E.02541
G1 X106.095 Y124.997 E.02123
G1 X105.74 Y124.572 E.02062
G1 X105.435 Y124.072 E.02183
G1 X105.14 Y123.306 E.03056
G1 X105.027 Y122.768 E.02048
G1 X104.99 Y122.223 E.02036
G1 X104.99 Y115.432 E.25293
G1 X104.921 Y115.144 E.01103
G1 X104.818 Y114.971 E.00749
G1 X104.673 Y114.863 E.00674
G1 X104.518 Y114.788 E.00639
G1 X104.289 Y114.735 E.00878
G1 X93.006 Y114.735 E.42025
G1 X92.413 Y114.692 E.02214
G1 X91.869 Y114.57 E.02075
G1 X90.995 Y114.191 E.0355
G1 X90.523 Y113.88 E.02105
G1 X90.095 Y113.497 E.02137
G1 X89.728 Y113.056 E.02137
G1 X89.434 Y112.57 E.02114
G1 X89.16 Y111.878 E.02775
G1 X89.027 Y111.267 E.02329
G1 X88.99 Y110.723 E.02031
G1 X88.99 Y100.78 E.37031
G1 X89.033 Y100.188 E.02214
G1 X89.163 Y99.619 E.02171
G1 X89.535 Y98.769 E.03456
G1 X89.845 Y98.297 E.02105
G1 X90.213 Y97.884 E.02062
G1 X90.669 Y97.503 E.02213
G1 X91.155 Y97.209 E.02114
G1 X91.847 Y96.935 E.02774
G1 X92.458 Y96.802 E.02328
G1 X92.993 Y96.765 E.01997
G1 X111.043 Y96.765 E.67229
G1 X111.331 Y96.696 E.01103
G1 X111.504 Y96.593 E.00749
G1 X111.612 Y96.448 E.00674
G1 X111.687 Y96.293 E.00639
G1 X111.74 Y96.064 E.00878
G1 X111.74 Y67.432 E1.06642
G1 X111.671 Y67.144 E.01103
G1 X111.568 Y66.971 E.00749
G1 X111.423 Y66.863 E.00674
M73 P26 R18
G1 X111.268 Y66.788 E.00639
G1 X111.039 Y66.735 E.00878
G1 X67.207 Y66.735 E1.63256
G1 X66.919 Y66.804 E.01103
G1 X66.746 Y66.907 E.00749
G1 X66.638 Y67.052 E.00675
G1 X66.563 Y67.207 E.00639
G1 X66.51 Y67.436 E.00878
G1 X66.51 Y94.719 E1.01619
G1 X66.467 Y95.312 E.02214
G1 X66.337 Y95.881 E.02171
G1 X65.966 Y96.731 E.03456
G1 X65.655 Y97.203 E.02105
G1 X65.272 Y97.63 E.02137
G1 X64.831 Y97.997 E.02137
G1 X64.345 Y98.291 E.02114
G1 X63.653 Y98.565 E.02774
G1 X63.022 Y98.701 E.02402
G1 X62.498 Y98.735 E.01957
G1 X59.556 Y98.735 E.10958
G1 X58.963 Y98.692 E.02214
G1 X58.415 Y98.57 E.0209
G1 X57.644 Y98.245 E.03115
G1 X57.087 Y97.891 E.02461
G1 X56.659 Y97.512 E.02128
G1 X56.278 Y97.056 E.02213
G1 X55.984 Y96.57 E.02114
G1 X55.71 Y95.878 E.02775
G1 X55.577 Y95.267 E.02329
G1 X55.54 Y94.723 E.02031
G1 X55.54 Y57.78 E1.37596
G1 X55.578 Y57.263 E.01932
M204 S6000
G1 X56.034 Y57.296 F42000
G1 F3000
M204 S500
G1 X56.036 Y57.265 E.00119
G1 X56.14 Y56.791 E.01804
G1 X56.431 Y56.093 E.02817
G1 X56.77 Y55.564 E.02341
G1 X57.103 Y55.193 E.01857
G1 X57.494 Y54.871 E.01884
G1 X57.919 Y54.616 E.01848
G1 X58.521 Y54.378 E.0241
G1 X59.063 Y54.258 E.02069
G1 X59.572 Y54.222 E.01902
G1 X118.683 Y54.222 E2.20163
G1 X119.21 Y54.261 E.01971
G1 X119.707 Y54.373 E.01895
G1 X120.403 Y54.667 E.02815
G1 X120.878 Y54.97 E.02099
G1 X121.255 Y55.301 E.01866
G1 X121.592 Y55.702 E.01954
G1 X121.857 Y56.142 E.01912
G1 X122.123 Y56.835 E.02764
G1 X122.22 Y57.304 E.01784
G1 X122.253 Y57.798 E.01843
G1 X122.253 Y102.608 E1.66902
G1 X122.271 Y102.915 E.01144
G1 X122.272 Y122.133 E.7158
G1 X122.215 Y122.786 E.0244
G1 X122.082 Y123.322 E.02059
G1 X121.866 Y123.843 E.02101
G1 X121.616 Y124.256 E.01798
G1 X121.321 Y124.617 E.01735
G1 X120.711 Y125.138 E.0299
G1 X120.283 Y125.398 E.01866
G1 X119.817 Y125.595 E.01885
G1 X119.333 Y125.718 E.01857
G1 X118.661 Y125.778 E.02516
G1 X109.007 Y125.777 E.35955
G1 X108.49 Y125.739 E.01934
G1 X108.016 Y125.635 E.01805
G1 X107.318 Y125.344 E.02817
G1 X106.789 Y125.005 E.02341
G1 X106.418 Y124.671 E.01859
G1 X106.107 Y124.297 E.01811
G1 X105.843 Y123.857 E.01911
G1 X105.583 Y123.187 E.02678
G1 X105.483 Y122.715 E.01797
G1 X105.447 Y122.203 E.01913
G1 X105.447 Y115.446 E.25167
G1 X105.367 Y115.045 E.01521
G1 X105.308 Y114.901 E.0058
G1 X105.217 Y114.749 E.0066
G1 X105.08 Y114.597 E.00763
G1 X104.954 Y114.503 E.00586
G1 X104.728 Y114.382 E.00956
G1 X104.396 Y114.291 E.0128
G1 X104.281 Y114.278 E.00432
G1 X93.027 Y114.278 E.41915
G1 X92.47 Y114.236 E.02083
G1 X91.999 Y114.129 E.01799
G1 X91.224 Y113.792 E.03148
G1 X90.811 Y113.522 E.01837
G1 X90.432 Y113.186 E.01885
G1 X90.096 Y112.781 E.01959
G1 X89.841 Y112.356 E.01848
G1 X89.603 Y111.754 E.0241
G1 X89.483 Y111.212 E.02069
G1 X89.447 Y110.703 E.01902
G1 X89.447 Y100.802 E.36875
G1 X89.486 Y100.266 E.02003
G1 X89.604 Y99.751 E.01967
G1 X89.944 Y98.978 E.03144
G1 X90.203 Y98.585 E.01756
G1 X90.525 Y98.22 E.01811
G1 X90.945 Y97.871 E.02033
G1 X91.369 Y97.616 E.01846
G1 X91.971 Y97.378 E.02408
G1 X92.513 Y97.258 E.02069
G1 X93.004 Y97.223 E.01834
G1 X111.029 Y97.222 E.67137
G1 X111.43 Y97.142 E.01521
G1 X111.574 Y97.083 E.0058
G1 X111.726 Y96.992 E.0066
G1 X111.876 Y96.857 E.00754
G1 X112.025 Y96.641 E.00976
G1 X112.134 Y96.387 E.0103
G1 X112.197 Y96.051 E.01273
G1 X112.197 Y67.446 E1.06544
G1 X112.117 Y67.045 E.01521
G1 X112.058 Y66.901 E.0058
G1 X111.967 Y66.749 E.0066
G1 X111.83 Y66.597 E.00763
G1 X111.704 Y66.503 E.00586
G1 X111.478 Y66.382 E.00956
G1 X111.146 Y66.291 E.0128
G1 X111.031 Y66.278 E.00432
G1 X67.221 Y66.278 E1.63176
G1 X66.82 Y66.358 E.01521
G1 X66.676 Y66.417 E.0058
G1 X66.524 Y66.508 E.0066
G1 X66.372 Y66.645 E.00763
G1 X66.278 Y66.771 E.00586
G1 X66.117 Y67.109 E.01394
G1 X66.053 Y67.449 E.01289
G1 X66.053 Y94.698 E1.01491
G1 X66.014 Y95.234 E.02004
G1 X65.896 Y95.749 E.01967
G1 X65.556 Y96.522 E.03144
G1 X65.285 Y96.931 E.01828
G1 X64.946 Y97.307 E.01884
G1 X64.556 Y97.629 E.01884
G1 X64.131 Y97.884 E.01848
G1 X63.53 Y98.122 E.02406
G1 X62.949 Y98.247 E.02216
G1 X62.478 Y98.278 E.01756
G1 X59.577 Y98.278 E.10805
G1 X59.04 Y98.239 E.02008
G1 X58.566 Y98.135 E.01804
G1 X57.868 Y97.844 E.0282
G1 X57.372 Y97.53 E.02185
G1 X56.981 Y97.185 E.01943
G1 X56.646 Y96.781 E.01954
G1 X56.391 Y96.356 E.01845
G1 X56.153 Y95.754 E.0241
G1 X56.033 Y95.212 E.02069
G1 X55.997 Y94.703 E.01902
G1 X55.997 Y57.802 E1.3744
G1 X56.029 Y57.356 E.01666
M204 S6000
G1 X56.485 Y57.389 F42000
G1 F3000
M204 S500
G1 X56.489 Y57.34 E.00182
G1 X56.575 Y56.942 E.0152
G1 X56.833 Y56.317 E.02516
G1 X57.142 Y55.833 E.02139
G1 X57.428 Y55.518 E.01586
G1 X57.767 Y55.24 E.01631
G1 X58.133 Y55.023 E.01584
G1 X58.645 Y54.82 E.02053
G1 X59.119 Y54.714 E.0181
G1 X59.593 Y54.679 E.01772
G1 X118.661 Y54.679 E2.20003
G1 X119.133 Y54.714 E.01764
G1 X119.578 Y54.814 E.01699
G1 X120.199 Y55.079 E.02515
G1 X120.594 Y55.331 E.01743
G1 X120.919 Y55.614 E.01606
G1 X121.212 Y55.961 E.01691
G1 X121.449 Y56.355 E.01712
G1 X121.685 Y56.974 E.0247
G1 X121.766 Y57.375 E.01522
G1 X121.796 Y57.818 E.01653
G1 X121.796 Y102.604 E1.66813
G1 X121.814 Y102.932 E.01223
G1 X121.815 Y122.107 E.7142
G1 X121.76 Y122.721 E.02294
G1 X121.642 Y123.188 E.01796
G1 X121.452 Y123.645 E.01845
G1 X121.247 Y123.984 E.01473
G1 X121.001 Y124.286 E.01452
G1 X120.433 Y124.772 E.02786
G1 X120.065 Y124.994 E.01599
G1 X119.661 Y125.163 E.01631
G1 X119.245 Y125.267 E.01596
G1 X118.634 Y125.321 E.02285
G1 X109.029 Y125.32 E.35773
G1 X108.566 Y125.286 E.01732
G1 X108.166 Y125.2 E.01521
G1 X107.542 Y124.942 E.02516
G1 X107.058 Y124.633 E.02139
G1 X106.742 Y124.346 E.0159
G1 X106.476 Y124.023 E.0156
G1 X106.25 Y123.644 E.01641
G1 X106.027 Y123.066 E.02309
G1 X105.939 Y122.661 E.01546
G1 X105.904 Y122.182 E.01788
G1 X105.904 Y115.458 E.25045
G1 X105.816 Y114.964 E.01867
G1 X105.734 Y114.737 E.009
G1 X105.55 Y114.435 E.01317
G1 X105.346 Y114.225 E.01091
G1 X105.164 Y114.097 E.00828
G1 X104.836 Y113.938 E.01357
G1 X104.526 Y113.853 E.01196
G1 X104.272 Y113.821 E.00954
G1 X93.05 Y113.821 E.418
G1 X92.528 Y113.78 E.01948
G1 X92.13 Y113.687 E.01522
G1 X91.452 Y113.393 E.02756
G1 X91.097 Y113.164 E.01571
G1 X90.77 Y112.874 E.01628
G1 X90.477 Y112.524 E.017
G1 X90.248 Y112.142 E.01658
G1 X90.045 Y111.63 E.02053
G1 X89.939 Y111.156 E.0181
G1 X89.904 Y110.682 E.01772
G1 X89.904 Y100.824 E.36716
M73 P27 R18
G1 X89.939 Y100.344 E.0179
G1 X90.045 Y99.883 E.01762
G1 X90.353 Y99.188 E.02833
G1 X90.574 Y98.856 E.01485
G1 X90.838 Y98.557 E.01485
G1 X91.219 Y98.239 E.01849
G1 X91.583 Y98.023 E.01575
G1 X92.095 Y97.82 E.02051
G1 X92.569 Y97.714 E.01812
G1 X93.025 Y97.68 E.01703
G1 X111.016 Y97.679 E.67007
G1 X111.612 Y97.561 E.02265
G1 X111.951 Y97.391 E.01411
G1 X112.178 Y97.2 E.01106
G1 X112.256 Y97.112 E.00436
G1 X112.449 Y96.812 E.01329
G1 X112.585 Y96.46 E.01404
G1 X112.654 Y96.04 E.01588
G1 X112.654 Y67.459 E1.06451
G1 X112.536 Y66.863 E.02265
G1 X112.367 Y66.526 E.01402
G1 X112.094 Y66.224 E.01519
G1 X111.912 Y66.096 E.00829
G1 X111.704 Y65.985 E.00876
G1 X111.274 Y65.853 E.01675
G1 X111.022 Y65.821 E.00946
G1 X67.233 Y65.821 E1.63099
G1 X66.741 Y65.908 E.01859
G1 X66.435 Y66.029 E.01227
G1 X66.21 Y66.176 E.01001
G1 X66.076 Y66.296 E.00672
G1 X65.859 Y66.587 E.01348
G1 X65.708 Y66.904 E.0131
G1 X65.666 Y67.032 E.005
G1 X65.596 Y67.46 E.01617
G1 X65.596 Y94.676 E1.01369
G1 X65.561 Y95.156 E.01791
G1 X65.463 Y95.592 E.01666
G1 X65.147 Y96.311 E.02927
G1 X64.916 Y96.658 E.01551
G1 X64.621 Y96.982 E.01632
G1 X64.283 Y97.26 E.0163
G1 X63.917 Y97.477 E.01584
G1 X63.407 Y97.679 E.02043
G1 X62.875 Y97.794 E.02028
G1 X62.459 Y97.821 E.01553
G1 X59.599 Y97.821 E.10652
G1 X59.115 Y97.786 E.01806
G1 X58.717 Y97.7 E.0152
G1 X58.09 Y97.441 E.02526
G1 X57.656 Y97.169 E.01906
G1 X57.303 Y96.857 E.01754
G1 X57.015 Y96.507 E.01692
G1 X56.798 Y96.142 E.01578
G1 X56.595 Y95.63 E.02053
G1 X56.489 Y95.156 E.0181
G1 X56.454 Y94.682 E.01772
G1 X56.454 Y57.824 E1.37281
G1 X56.481 Y57.449 E.014
M204 S6000
G1 X56.937 Y57.481 F42000
G1 F3000
M204 S500
G1 X56.942 Y57.415 E.00248
G1 X57.011 Y57.09 E.01237
G1 X57.235 Y56.54 E.02212
G1 X57.514 Y56.103 E.01932
G1 X57.752 Y55.844 E.01311
G1 X58.039 Y55.61 E.01377
G1 X58.345 Y55.431 E.01321
G1 X58.791 Y55.256 E.01783
G1 X59.196 Y55.166 E.01548
G1 X59.615 Y55.136 E.01564
G1 X118.639 Y55.137 E2.19842
G1 X119.056 Y55.166 E.01555
G1 X119.448 Y55.256 E.015
G1 X119.995 Y55.491 E.02216
G1 X120.311 Y55.692 E.01395
G1 X120.585 Y55.929 E.01348
G1 X120.845 Y56.237 E.01504
G1 X121.041 Y56.567 E.01427
G1 X121.247 Y57.113 E.02174
G1 X121.313 Y57.445 E.0126
G1 X121.339 Y57.837 E.01465
G1 X121.339 Y102.601 E1.66726
G1 X121.357 Y102.949 E.01297
G1 X121.358 Y122.081 E.71261
G1 X121.306 Y122.655 E.02146
G1 X121.204 Y123.053 E.01531
G1 X121.038 Y123.447 E.01592
G1 X120.877 Y123.712 E.01154
G1 X120.68 Y123.956 E.01169
G1 X120.154 Y124.406 E.02579
G1 X119.849 Y124.589 E.01327
G1 X119.507 Y124.73 E.01377
G1 X119.158 Y124.816 E.01336
G1 X118.608 Y124.864 E.02059
G1 X109.051 Y124.863 E.35594
G1 X108.641 Y124.833 E.01534
G1 X108.315 Y124.764 E.01239
G1 X107.765 Y124.54 E.02212
G1 X107.328 Y124.261 E.01932
G1 X107.081 Y124.036 E.01243
G1 X106.857 Y123.767 E.01305
G1 X106.658 Y123.433 E.01449
G1 X106.47 Y122.944 E.0195
G1 X106.394 Y122.605 E.01296
G1 X106.361 Y122.161 E.01659
G1 X106.352 Y115.367 E.25303
G1 X106.243 Y114.801 E.02148
G1 X106.119 Y114.49 E.01248
G1 X105.87 Y114.109 E.01694
G1 X105.601 Y113.846 E.01402
G1 X105.356 Y113.683 E.01094
G1 X104.947 Y113.495 E.01677
G1 X104.576 Y113.399 E.01429
G1 X104.265 Y113.364 E.01166
G1 X93.073 Y113.364 E.41685
G1 X92.588 Y113.325 E.01811
G1 X92.263 Y113.247 E.01245
G1 X91.678 Y112.993 E.02375
G1 X91.383 Y112.804 E.01306
G1 X91.106 Y112.562 E.01371
G1 X90.858 Y112.267 E.01435
G1 X90.655 Y111.929 E.01467
G1 X90.487 Y111.505 E.017
G1 X90.391 Y111.079 E.01627
G1 X90.361 Y110.66 E.01564
G1 X90.361 Y100.845 E.36556
G1 X90.391 Y100.423 E.01576
G1 X90.486 Y100.017 E.01554
G1 X90.762 Y99.399 E.02521
G1 X90.943 Y99.128 E.01216
G1 X91.15 Y98.894 E.01164
G1 X91.493 Y98.608 E.01663
G1 X91.795 Y98.431 E.01303
G1 X92.24 Y98.256 E.01781
G1 X92.647 Y98.166 E.01551
G1 X93.048 Y98.137 E.01496
G1 X111.003 Y98.136 E.66879
G1 X111.693 Y98.01 E.02611
G1 X111.826 Y97.965 E.00522
G1 X112.144 Y97.805 E.01327
G1 X112.468 Y97.553 E.01528
G1 X112.593 Y97.42 E.00682
G1 X112.879 Y96.966 E.01998
G1 X113.038 Y96.523 E.01751
G1 X113.111 Y96.03 E.01859
G1 X113.111 Y67.472 E1.06367
G1 X112.985 Y66.782 E.02612
G1 X112.94 Y66.65 E.00521
G1 X112.779 Y66.33 E.01333
G1 X112.701 Y66.215 E.00518
G1 X112.346 Y65.843 E.01915
G1 X112.12 Y65.689 E.01019
G1 X111.93 Y65.587 E.00804
G1 X111.418 Y65.419 E.02006
G1 X111.013 Y65.364 E.01523
G1 X67.244 Y65.364 E1.63024
G1 X66.674 Y65.456 E.0215
M73 P27 R17
G1 X66.174 Y65.653 E.02002
G1 X65.968 Y65.788 E.00916
G1 X65.778 Y65.95 E.00929
G1 X65.441 Y66.402 E.02103
G1 X65.299 Y66.701 E.01233
G1 X65.235 Y66.882 E.00713
G1 X65.139 Y67.471 E.02225
G1 X65.139 Y94.655 E1.01247
G1 X65.109 Y95.078 E.01582
G1 X65.03 Y95.435 E.01362
G1 X64.738 Y96.101 E.02707
G1 X64.547 Y96.383 E.01269
G1 X64.298 Y96.657 E.0138
G1 X64.011 Y96.89 E.01376
G1 X63.705 Y97.069 E.01322
G1 X63.263 Y97.242 E.01768
G1 X62.801 Y97.341 E.01758
G1 X62.44 Y97.364 E.01349
G1 X59.62 Y97.364 E.10501
G1 X59.171 Y97.331 E.01679
G1 X58.842 Y97.257 E.01256
G1 X58.29 Y97.027 E.02226
G1 X57.922 Y96.794 E.01621
G1 X57.626 Y96.531 E.01478
G1 X57.384 Y96.234 E.01426
G1 X57.206 Y95.93 E.01313
G1 X57.031 Y95.484 E.01783
G1 X56.941 Y95.079 E.01548
G1 X56.911 Y94.66 E.01564
G1 X56.911 Y57.845 E1.3712
G1 X56.933 Y57.541 E.01135
; WIPE_START
G1 X56.942 Y57.415 E-.04807
G1 X57.011 Y57.09 E-.12616
G1 X57.235 Y56.54 E-.22569
G1 X57.514 Y56.103 E-.19707
G1 X57.752 Y55.844 E-.1338
G1 X57.812 Y55.795 E-.0292
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X62.71 Y61.648 Z.6 F42000
G1 X106.014 Y113.39 Z.6
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X106.096 Y113.362 E.00325
G1 X106.225 Y113.363 E.00479
G1 X106.329 Y113.41 E.00426
G1 X106.362 Y113.5 E.00354
G1 X106.362 Y113.625 E.00469
G1 X106.314 Y113.729 E.00426
G1 X106.204 Y113.761 E.00426
G1 X106.129 Y113.724 E.00314
G1 X106 Y113.597 E.00671
G1 X105.959 Y113.491 E.00426
G1 X105.985 Y113.443 E.00203
; WIPE_START
G1 X106.096 Y113.362 E-.08254
G1 X106.225 Y113.363 E-.07737
G1 X106.329 Y113.41 E-.06882
G1 X106.362 Y113.5 E-.05715
G1 X106.362 Y113.625 E-.07575
G1 X106.314 Y113.729 E-.06882
G1 X106.204 Y113.761 E-.06882
G1 X106.129 Y113.724 E-.05078
G1 X106 Y113.597 E-.10843
G1 X105.959 Y113.491 E-.06882
G1 X105.985 Y113.443 E-.03272
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X109.111 Y106.48 Z.6 F42000
G1 X112.858 Y98.136 Z.6
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X112.754 Y98.088 E.00426
G1 X112.722 Y97.978 E.00426
G1 X112.761 Y97.902 E.00317
G1 X112.877 Y97.785 E.00614
G1 X112.984 Y97.745 E.00426
G1 X113.084 Y97.8 E.00426
G1 X113.111 Y97.882 E.00321
G1 X113.111 Y97.999 E.00436
G1 X113.063 Y98.103 E.00426
G1 X112.974 Y98.136 E.00355
G1 X112.918 Y98.136 E.00209
; WIPE_START
G1 X112.754 Y98.088 E-.10525
G1 X112.722 Y97.978 E-.07051
G1 X112.761 Y97.902 E-.05243
G1 X112.877 Y97.785 E-.10165
G1 X112.984 Y97.745 E-.0705
G1 X113.084 Y97.8 E-.07051
G1 X113.111 Y97.882 E-.0531
G1 X113.111 Y97.999 E-.07218
G1 X113.063 Y98.103 E-.07051
G1 X112.974 Y98.136 E-.05876
G1 X112.918 Y98.136 E-.0346
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X112.926 Y90.504 Z.6 F42000
G1 X112.953 Y65.776 Z.6
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X112.875 Y65.735 E.0033
G1 X112.742 Y65.596 E.00715
G1 X112.705 Y65.487 E.00426
G1 X112.763 Y65.389 E.00426
G1 X112.842 Y65.364 E.00307
G1 X112.974 Y65.364 E.00493
G1 X113.078 Y65.412 E.00426
G1 X113.111 Y65.501 E.00355
G1 X113.111 Y65.64 E.00518
G1 X113.063 Y65.744 E.00426
G1 X113.011 Y65.759 E.00203
; WIPE_START
G1 X112.875 Y65.735 E-.08149
G1 X112.742 Y65.596 E-.11296
G1 X112.705 Y65.487 E-.0673
G1 X112.763 Y65.389 E-.0673
G1 X112.842 Y65.364 E-.04854
G1 X112.974 Y65.364 E-.07795
G1 X113.078 Y65.412 E-.0673
G1 X113.111 Y65.501 E-.05609
G1 X113.111 Y65.64 E-.08176
G1 X113.063 Y65.744 E-.0673
G1 X113.011 Y65.759 E-.03201
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X105.379 Y65.721 Z.6 F42000
G1 X65.525 Y65.522 Z.6
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X65.489 Y65.595 E.00303
G1 X65.385 Y65.713 E.00587
G1 X65.285 Y65.767 E.00426
G1 X65.177 Y65.727 E.00426
G1 X65.138 Y65.63 E.00389
G1 X65.138 Y65.501 E.00483
G1 X65.186 Y65.397 E.00426
G1 X65.275 Y65.364 E.00355
G1 X65.389 Y65.364 E.00425
G1 X65.493 Y65.412 E.00426
G1 X65.508 Y65.464 E.00203
M204 S6000
G1 X65.508 Y64.907 F42000
G1 F3000
M204 S500
G1 X64.819 Y64.907 E.02569
G1 X64.715 Y64.955 E.00426
G1 X64.681 Y65.044 E.00355
G1 X64.65 Y95.028 E1.1168
G1 X64.563 Y95.393 E.01399
G1 X64.459 Y95.655 E.01048
G1 X64.161 Y96.116 E.02045
G1 X63.771 Y96.484 E.01997
G1 X63.656 Y96.562 E.00517
G1 X63.16 Y96.796 E.02041
G1 X62.88 Y96.865 E.01077
G1 X62.49 Y96.907 E.01459
G1 X59.553 Y96.907 E.10942
G1 X59.292 Y96.886 E.00974
G1 X58.811 Y96.763 E.0185
G1 X58.506 Y96.627 E.01241
G1 X58.036 Y96.272 E.02195
G1 X57.893 Y96.127 E.00757
G1 X57.662 Y95.795 E.01508
G1 X57.509 Y95.471 E.01332
G1 X57.409 Y95.103 E.01423
G1 X57.368 Y94.715 E.01451
G1 X57.368 Y57.791 E1.3753
G1 X57.424 Y57.342 E.01686
G1 X57.528 Y56.983 E.01391
G1 X57.723 Y56.612 E.01562
G1 X58.005 Y56.258 E.01684
G1 X58.367 Y55.958 E.0175
G1 X58.71 Y55.773 E.01452
G1 X59.078 Y55.654 E.0144
G1 X59.561 Y55.593 E.01815
G1 X118.684 Y55.593 E2.20211
G1 X119.129 Y55.649 E.01671
G1 X119.598 Y55.799 E.01835
G1 X119.945 Y56.004 E.01499
G1 X120.22 Y56.232 E.01333
G1 X120.356 Y56.372 E.00727
G1 X120.588 Y56.705 E.01511
G1 X120.741 Y57.029 E.01332
G1 X120.84 Y57.397 E.01422
G1 X120.882 Y57.785 E.01453
G1 X120.882 Y102.617 E1.66983
G1 X120.901 Y102.904 E.01072
G1 X120.901 Y122.155 E.71703
M73 P28 R17
G1 X120.85 Y122.588 E.01625
G1 X120.699 Y123.072 E.01889
G1 X120.491 Y123.443 E.01581
G1 X120.136 Y123.845 E.01999
G1 X119.878 Y124.04 E.01206
G1 X119.536 Y124.221 E.01439
G1 X119.229 Y124.321 E.01204
G1 X118.674 Y124.407 E.02089
G1 X109.007 Y124.407 E.36008
G1 X108.623 Y124.363 E.01438
G1 X108.14 Y124.216 E.01884
G1 X107.841 Y124.058 E.01258
G1 X107.609 Y123.888 E.01071
G1 X107.258 Y123.52 E.01894
G1 X107.151 Y123.357 E.00726
G1 X106.927 Y122.88 E.01963
G1 X106.86 Y122.61 E.01036
G1 X106.828 Y122.367 E.00914
G1 X106.818 Y113.043 E.34726
G1 X106.771 Y112.939 E.00426
G1 X106.682 Y112.906 E.00354
G1 X92.731 Y112.882 E.51961
G1 X92.386 Y112.807 E.01316
G1 X92.038 Y112.67 E.01392
G1 X91.75 Y112.492 E.01262
G1 X91.397 Y112.182 E.01748
G1 X91.184 Y111.91 E.01288
G1 X90.996 Y111.562 E.01472
G1 X90.914 Y111.318 E.00961
G1 X90.835 Y110.904 E.01567
G1 X90.835 Y100.6 E.38379
G1 X90.948 Y100.082 E.01976
G1 X91.184 Y99.594 E.02019
G1 X91.521 Y99.187 E.01966
G1 X91.739 Y99.006 E.01057
G1 X91.947 Y98.875 E.00913
G1 X92.398 Y98.688 E.01821
G1 X92.52 Y98.656 E.00468
G1 X93.013 Y98.593 E.0185
G1 X113.431 Y98.593 E.76051
G1 X113.535 Y98.545 E.00426
G1 X113.568 Y98.456 E.00355
G1 X113.568 Y65.044 E1.24447
G1 X113.52 Y64.94 E.00426
G1 X113.431 Y64.907 E.00355
G1 X65.568 Y64.907 E1.78271
M204 S6000
G1 X65.568 Y64.45 F42000
G1 F3000
M204 S500
G1 X64.362 Y64.45 E.04494
G1 X64.258 Y64.497 E.00426
G1 X64.225 Y64.587 E.00355
G1 X64.205 Y94.924 E1.12995
G1 X64.141 Y95.216 E.01112
G1 X64.029 Y95.499 E.01134
G1 X63.78 Y95.863 E.01645
G1 X63.459 Y96.149 E.016
G1 X63.052 Y96.352 E.01694
G1 X62.835 Y96.41 E.00839
G1 X62.498 Y96.45 E.01264
G1 X59.547 Y96.45 E.1099
G1 X59.323 Y96.43 E.00839
G1 X58.923 Y96.32 E.01545
G1 X58.693 Y96.21 E.00947
G1 X58.314 Y95.91 E.01802
G1 X58.223 Y95.812 E.00496
G1 X58.037 Y95.533 E.01249
G1 X57.923 Y95.277 E.01042
G1 X57.864 Y95.059 E.00841
G1 X57.825 Y94.723 E.01263
G1 X57.825 Y57.782 E1.37589
G1 X57.878 Y57.395 E.01457
G1 X57.968 Y57.108 E.01116
G1 X58.125 Y56.828 E.01199
G1 X58.364 Y56.541 E.0139
G1 X58.656 Y56.312 E.01382
G1 X58.923 Y56.177 E.01116
G1 X59.217 Y56.089 E.01143
G1 X59.552 Y56.05 E.01256
G1 X118.693 Y56.05 E2.20275
G1 X119.078 Y56.103 E.0145
G1 X119.461 Y56.235 E.01507
G1 X119.645 Y56.349 E.00805
G1 X119.934 Y56.589 E.01401
G1 X120.027 Y56.688 E.00506
G1 X120.213 Y56.967 E.01248
G1 X120.327 Y57.223 E.01042
G1 X120.385 Y57.44 E.0084
G1 X120.425 Y57.777 E.01264
G1 X120.425 Y102.639 E1.6709
G1 X120.444 Y102.9 E.00975
G1 X120.444 Y122.163 E.7175
G1 X120.396 Y122.542 E.01424
G1 X120.262 Y122.937 E.0155
G1 X120.094 Y123.217 E.01217
G1 X119.861 Y123.48 E.01308
G1 X119.662 Y123.638 E.00946
G1 X119.393 Y123.788 E.01147
G1 X119.161 Y123.869 E.00915
G1 X118.685 Y123.95 E.01799
G1 X108.999 Y123.95 E.36076
G1 X108.669 Y123.909 E.01241
G1 X108.273 Y123.779 E.01553
G1 X108.062 Y123.659 E.00903
G1 X107.878 Y123.519 E.00859
G1 X107.638 Y123.266 E.01299
G1 X107.564 Y123.16 E.00481
G1 X107.372 Y122.772 E.01615
G1 X107.314 Y122.559 E.00822
G1 X107.28 Y122.299 E.00976
G1 X107.275 Y112.587 E.36173
G1 X107.227 Y112.483 E.00426
G1 X107.138 Y112.45 E.00354
G1 X92.832 Y112.436 E.53287
G1 X92.549 Y112.38 E.01071
G1 X92.277 Y112.281 E.01078
G1 X92.048 Y112.146 E.00992
G1 X91.765 Y111.911 E.0137
G1 X91.537 Y111.619 E.01379
G1 X91.401 Y111.349 E.01126
G1 X91.364 Y111.243 E.0042
G1 X91.282 Y110.807 E.01651
G1 X91.282 Y100.695 E.37662
G1 X91.36 Y100.281 E.01572
G1 X91.537 Y99.883 E.01621
G1 X91.803 Y99.547 E.01596
G1 X92.038 Y99.352 E.01138
G1 X92.186 Y99.265 E.00639
G1 X92.575 Y99.109 E.01558
G1 X93.004 Y99.05 E.01614
G1 X113.888 Y99.05 E.77786
G1 X113.992 Y99.003 E.00426
G1 X114.025 Y98.913 E.00355
G1 X114.025 Y64.587 E1.27852
G1 X113.978 Y64.483 E.00426
G1 X113.888 Y64.45 E.00355
G1 X65.628 Y64.45 E1.7975
M204 S6000
G1 X65.628 Y63.993 F42000
G1 F3000
M204 S500
G1 X63.905 Y63.993 E.06419
G1 X63.801 Y64.04 E.00426
G1 X63.768 Y64.13 E.00355
G1 X63.758 Y94.832 E1.14354
G1 X63.721 Y95.037 E.00775
G1 X63.601 Y95.339 E.01209
G1 X63.405 Y95.601 E.0122
G1 X63.227 Y95.756 E.00878
G1 X63.126 Y95.819 E.00445
G1 X62.925 Y95.913 E.00826
G1 X62.783 Y95.956 E.00551
G1 X62.506 Y95.993 E.01044
G1 X59.541 Y95.993 E.11043
G1 X59.359 Y95.974 E.00679
G1 X59.045 Y95.88 E.01222
G1 X58.899 Y95.802 E.00617
G1 X58.601 Y95.554 E.01445
G1 X58.454 Y95.347 E.00944
G1 X58.362 Y95.15 E.0081
G1 X58.319 Y95.008 E.00552
G1 X58.282 Y94.731 E.01043
G1 X58.282 Y57.773 E1.37653
G1 X58.331 Y57.455 E.01198
G1 X58.403 Y57.247 E.00819
G1 X58.469 Y57.129 E.00504
G1 X58.721 Y56.826 E.0147
G1 X58.928 Y56.679 E.00943
G1 X59.125 Y56.587 E.0081
G1 X59.267 Y56.544 E.00552
G1 X59.544 Y56.507 E.01043
G1 X118.702 Y56.507 E2.2034
G1 X119.02 Y56.556 E.01198
G1 X119.228 Y56.628 E.00819
G1 X119.346 Y56.694 E.00504
G1 X119.649 Y56.946 E.0147
M73 P29 R17
G1 X119.796 Y57.153 E.00943
G1 X119.888 Y57.35 E.0081
G1 X119.931 Y57.492 E.00552
G1 X119.968 Y57.769 E.01044
G1 X119.968 Y102.663 E1.67211
G1 X119.987 Y102.894 E.00865
G1 X119.987 Y122.172 E.71801
G1 X119.942 Y122.49 E.01197
G1 X119.831 Y122.787 E.01181
G1 X119.752 Y122.915 E.0056
G1 X119.573 Y123.125 E.01028
G1 X119.438 Y123.239 E.00659
G1 X119.231 Y123.361 E.00894
G1 X119.084 Y123.419 E.00587
G1 X118.697 Y123.493 E.0147
G1 X108.991 Y123.493 E.36151
G1 X108.809 Y123.474 E.00679
G1 X108.495 Y123.38 E.01222
G1 X108.346 Y123.301 E.00628
G1 X108.147 Y123.149 E.00934
G1 X107.972 Y122.955 E.00972
G1 X107.811 Y122.647 E.01294
G1 X107.769 Y122.508 E.0054
G1 X107.732 Y122.231 E.01043
G1 X107.732 Y112.13 E.37621
G1 X107.685 Y112.026 E.00426
G1 X107.595 Y111.993 E.00355
G1 X92.921 Y111.988 E.54657
G1 X92.702 Y111.949 E.00828
G1 X92.497 Y111.881 E.00804
G1 X92.349 Y111.802 E.00626
G1 X92.051 Y111.554 E.01445
G1 X91.904 Y111.347 E.00944
G1 X91.812 Y111.15 E.0081
G1 X91.739 Y110.82 E.0126
G1 X91.732 Y100.773 E.3742
G1 X91.78 Y100.461 E.01174
G1 X91.899 Y100.162 E.01202
G1 X92.095 Y99.899 E.0122
G1 X92.273 Y99.744 E.00878
G1 X92.374 Y99.681 E.00446
G1 X92.575 Y99.587 E.00826
G1 X92.717 Y99.544 E.00551
G1 X92.994 Y99.507 E.01044
G1 X114.345 Y99.507 E.79523
G1 X114.449 Y99.46 E.00426
G1 X114.482 Y99.37 E.00355
G1 X114.482 Y64.13 E1.31257
G1 X114.435 Y64.026 E.00426
G1 X114.345 Y63.993 E.00355
G1 X65.688 Y63.993 E1.81228
M204 S6000
G1 X65.688 Y63.536 F42000
G1 F3000
M204 S500
G1 X63.448 Y63.536 E.08345
G1 X63.344 Y63.583 E.00426
G1 X63.311 Y63.673 E.00355
G1 X63.311 Y94.738 E1.15705
G1 X63.268 Y94.968 E.00872
G1 X63.181 Y95.159 E.00783
G1 X63.052 Y95.311 E.00743
G1 X62.939 Y95.402 E.00541
G1 X62.722 Y95.504 E.00892
G1 X62.514 Y95.536 E.00782
G1 X59.534 Y95.536 E.11102
G1 X59.407 Y95.52 E.00475
G1 X59.182 Y95.444 E.00884
G1 X58.964 Y95.277 E.01023
G1 X58.873 Y95.164 E.00541
G1 X58.771 Y94.947 E.00893
G1 X58.739 Y94.739 E.00782
G1 X58.739 Y57.762 E1.37725
G1 X58.782 Y57.529 E.00884
G1 X58.829 Y57.411 E.00475
G1 X58.998 Y57.189 E.01037
G1 X59.111 Y57.098 E.00541
G1 X59.328 Y56.996 E.00893
G1 X59.536 Y56.964 E.00782
G1 X118.713 Y56.964 E2.20412
G1 X118.946 Y57.007 E.00884
G1 X119.064 Y57.054 E.00475
G1 X119.286 Y57.223 E.01037
G1 X119.377 Y57.336 E.00541
G1 X119.479 Y57.553 E.00892
G1 X119.511 Y57.761 E.00782
G1 X119.511 Y102.691 E1.67349
G1 X119.53 Y102.889 E.00739
G1 X119.53 Y122.181 E.71858
G1 X119.489 Y122.427 E.00927
G1 X119.409 Y122.612 E.0075
G1 X119.217 Y122.839 E.01109
G1 X118.991 Y122.972 E.00976
G1 X118.71 Y123.036 E.01074
G1 X108.984 Y123.036 E.36225
G1 X108.857 Y123.02 E.00475
G1 X108.632 Y122.944 E.00884
G1 X108.414 Y122.777 E.01023
G1 X108.323 Y122.664 E.00541
G1 X108.221 Y122.447 E.00893
G1 X108.189 Y122.239 E.00782
G1 X108.189 Y111.673 E.39357
G1 X108.142 Y111.569 E.00426
G1 X108.052 Y111.536 E.00355
G1 X92.984 Y111.536 E.56125
G1 X92.857 Y111.52 E.00475
G1 X92.632 Y111.444 E.00884
G1 X92.414 Y111.277 E.01023
G1 X92.323 Y111.164 E.00541
G1 X92.221 Y110.947 E.00893
G1 X92.189 Y110.739 E.00782
G1 X92.189 Y100.762 E.37161
G1 X92.232 Y100.532 E.00872
G1 X92.319 Y100.341 E.00783
G1 X92.448 Y100.189 E.00743
G1 X92.561 Y100.098 E.00541
G1 X92.778 Y99.996 E.00892
G1 X92.986 Y99.964 E.00782
G1 X114.802 Y99.964 E.81259
G1 X114.906 Y99.917 E.00426
G1 X114.939 Y99.827 E.00355
G1 X114.939 Y63.673 E1.34662
G1 X114.892 Y63.569 E.00426
G1 X114.802 Y63.536 E.00355
G1 X65.748 Y63.536 E1.82707
M204 S6000
G1 X65.748 Y63.079 F42000
G1 F3000
M204 S500
G1 X62.854 Y63.079 E.10782
G1 X62.854 Y94.75 E1.17964
G1 X62.825 Y94.861 E.00426
G1 X62.778 Y94.945 E.00361
G1 X62.641 Y95.054 E.00651
G1 X62.525 Y95.079 E.00442
G1 X59.525 Y95.079 E.11174
G1 X59.414 Y95.05 E.00426
G1 X59.33 Y95.003 E.00361
G1 X59.221 Y94.866 E.00651
G1 X59.196 Y94.75 E.00442
G1 X59.196 Y57.75 E1.37811
G1 X59.225 Y57.639 E.00426
G1 X59.272 Y57.555 E.00361
G1 X59.409 Y57.446 E.00651
G1 X59.525 Y57.421 E.00442
G1 X118.725 Y57.421 E2.20498
G1 X118.836 Y57.45 E.00426
G1 X118.92 Y57.497 E.00361
G1 X119.029 Y57.634 E.00651
G1 X119.054 Y57.75 E.00442
G1 X119.054 Y102.727 E1.67524
G1 X119.072 Y102.882 E.0058
G1 X119.072 Y122.193 E.71925
G1 X119.041 Y122.341 E.00565
G1 X118.954 Y122.467 E.00568
G1 X118.859 Y122.535 E.00436
G1 X118.725 Y122.579 E.00524
G1 X108.975 Y122.579 E.36315
M73 P30 R17
G1 X108.864 Y122.55 E.00426
G1 X108.78 Y122.503 E.00361
G1 X108.671 Y122.366 E.00651
G1 X108.646 Y122.25 E.00442
G1 X108.646 Y111.079 E.41609
G1 X92.975 Y111.079 E.5837
G1 X92.864 Y111.05 E.00426
G1 X92.78 Y111.003 E.00361
G1 X92.671 Y110.866 E.00651
G1 X92.646 Y110.75 E.00442
G1 X92.646 Y100.75 E.37246
G1 X92.675 Y100.639 E.00426
G1 X92.722 Y100.555 E.00361
G1 X92.859 Y100.446 E.00651
G1 X92.975 Y100.421 E.00442
G1 X115.396 Y100.421 E.83511
G1 X115.396 Y63.079 E1.39088
G1 X65.808 Y63.079 E1.84697
; WIPE_START
G1 X63.808 Y63.079 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X62.275 Y62.5 Z.6 F42000
G1 Z.2
G1 E.8 F1800
; FEATURE: Outer wall
G1 F3000
M204 S500
G1 X62.275 Y94.5 E1.19188
G1 X59.775 Y94.5 E.09312
G1 X59.775 Y58 E1.35949
G1 X118.475 Y58 E2.18635
G1 X118.475 Y102.768 E1.66743
G1 X118.494 Y102.9 E.00496
G1 X118.494 Y122 E.71141
G1 X109.225 Y122 E.34523
G1 X109.225 Y110.5 E.42833
G1 X93.225 Y110.5 E.59594
G1 X93.225 Y101 E.35384
G1 X115.975 Y101 E.84735
G1 X115.975 Y62.5 E1.43398
G1 X62.335 Y62.5 E1.99789
M204 S6000
G1 X61.818 Y62.043 F42000
; FEATURE: Inner wall
G1 F3000
M204 S500
G1 X61.818 Y94.043 E1.19188
G1 X60.232 Y94.043 E.05907
G1 X60.232 Y58.457 E1.32544
G1 X118.018 Y58.457 E2.1523
G1 X118.018 Y102.801 E1.65162
G1 X118.037 Y102.932 E.00496
G1 X118.037 Y121.543 E.69317
G1 X109.682 Y121.543 E.31118
G1 X109.682 Y110.043 E.42833
G1 X93.682 Y110.043 E.59594
G1 X93.682 Y101.457 E.31979
G1 X116.432 Y101.457 E.84735
G1 X116.432 Y62.043 E1.46803
G1 X61.878 Y62.043 E2.03193
M204 S6000
G1 X61.361 Y61.586 F42000
G1 F3000
M204 S500
G1 X61.361 Y93.586 E1.19188
G1 X60.689 Y93.586 E.02502
G1 X60.689 Y58.914 E1.29139
G1 X117.561 Y58.914 E2.11826
G1 X117.561 Y102.833 E1.63582
G1 X117.58 Y102.965 E.00496
G1 X117.58 Y121.086 E.67493
G1 X110.139 Y121.086 E.27714
G1 X110.139 Y109.586 E.42833
G1 X94.139 Y109.586 E.59594
G1 X94.139 Y101.914 E.28574
G1 X116.889 Y101.914 E.84735
M73 P31 R17
G1 X116.889 Y61.586 E1.50208
G1 X61.421 Y61.586 E2.06598
M204 S6000
G1 X61.146 Y61.129 F42000
G1 F3000
M204 S500
G1 X61.146 Y59.371 E.06546
G1 X117.104 Y59.371 E2.08421
G1 X117.104 Y61.129 E.06546
G1 X61.206 Y61.129 E2.08197
M204 S6000
G1 X61.603 Y60.672 F42000
G1 F3000
M204 S500
G1 X61.603 Y59.828 E.03142
G1 X116.647 Y59.828 E2.05016
G1 X116.647 Y60.672 E.03142
G1 X61.663 Y60.672 E2.04792
; WIPE_START
G1 X61.603 Y59.828 E-.32132
G1 X62.758 Y59.828 E-.43868
; WIPE_END
G1 E-.04 F1800
M204 S6000
M73 P31 R16
G1 X68.459 Y64.903 Z.6 F42000
G1 X110.553 Y102.371 Z.6
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X117.104 Y102.371 E.244
G1 X117.104 Y102.866 E.01842
G1 X117.123 Y102.998 E.00496
G1 X117.123 Y120.629 E.65669
G1 X110.596 Y120.629 E.24309
G1 X110.596 Y109.129 E.42833
G1 X110.553 Y109.129 E.00162
G1 X110.512 Y108.903 E.00854
G2 X110.512 Y102.597 I-1.029 J-3.153 E.31017
G1 X110.542 Y102.43 E.0063
; WIPE_START
M73 P32 R16
G1 X112.542 Y102.412 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X111.891 Y102.828 Z.6 F42000
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X116.637 Y102.828 E.17677
G1 X116.666 Y103.03 E.0076
G1 X116.666 Y120.172 E.63846
G1 X111.053 Y120.172 E.20904
G1 X111.053 Y109.188 E.4091
G2 X112.335 Y103.273 I-1.601 J-3.443 E.26085
G1 X111.933 Y102.871 E.02118
; WIPE_START
G1 X113.933 Y102.853 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X112.948 Y103.285 Z.6 F42000
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X116.209 Y103.285 E.12146
G1 X116.209 Y119.715 E.61193
G1 X111.51 Y119.715 E.17499
G1 X111.51 Y109.459 E.38197
G1 X111.771 Y109.317 E.01107
G2 X113.333 Y103.985 I-2.308 J-3.57 E.22551
G1 X112.976 Y103.338 E.02751
; WIPE_START
G1 X114.976 Y103.305 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X110.292 Y107.521 Z.6 F42000
G1 Z.2
G1 E.8 F1800
; FEATURE: Outer wall
G1 F3000
M204 S500
G1 X110.282 Y107.519 E.00038
G3 X109.198 Y103.819 I-.81 J-1.771 E.24882
G1 X109.468 Y103.8 E.01008
G3 X110.526 Y107.386 I.004 J1.948 E.18657
G1 X110.344 Y107.491 E.00782
M204 S6000
G1 X110.511 Y107.922 F42000
; FEATURE: Inner wall
G1 F3000
M204 S500
G1 X110.472 Y107.935 E.00154
G3 X109.133 Y103.366 I-1 J-2.188 E.30724
G1 X109.467 Y103.342 E.01249
G3 X110.774 Y107.77 I.004 J2.405 E.23037
G1 X110.563 Y107.892 E.00907
M204 S6000
G1 X110.73 Y108.323 F42000
G1 F3000
M204 S500
G1 X110.661 Y108.35 E.00275
G3 X109.068 Y102.912 I-1.19 J-2.604 E.36567
G1 X109.467 Y102.883 E.01489
G3 X111.021 Y108.154 I.005 J2.863 E.27418
G1 X110.782 Y108.293 E.01032
; WIPE_START
G1 X110.661 Y108.35 E-.0507
G1 X110.282 Y108.501 E-.15514
G1 X109.891 Y108.586 E-.15185
G1 X109.476 Y108.617 E-.15826
G1 X109.066 Y108.588 E-.15623
G1 X108.84 Y108.539 E-.08782
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X108.439 Y108.903 Z.6 F42000
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X108.399 Y109.129 E.00855
G1 X98.553 Y109.129 E.36673
G1 X98.512 Y108.903 E.00854
G2 X98.512 Y102.597 I-1.028 J-3.153 E.3102
G1 X98.553 Y102.371 E.00854
G1 X108.397 Y102.371 E.36667
G1 X108.438 Y102.597 E.00854
G2 X108.382 Y108.884 I1.028 J3.153 E.30797
; WIPE_START
G1 X108.399 Y109.129 E-.09335
G1 X106.645 Y109.129 E-.66665
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X107.06 Y108.672 Z.6 F42000
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X99.89 Y108.672 E.26702
G1 X100.334 Y108.228 E.02339
G2 X100.338 Y103.275 I-2.873 J-2.478 E.20097
G1 X99.89 Y102.828 E.02355
G1 X107.06 Y102.828 E.26703
G1 X106.617 Y103.271 E.02334
G2 X106.623 Y108.235 I2.862 J2.478 E.20162
G1 X107.017 Y108.629 E.02078
; WIPE_START
G1 X105.017 Y108.641 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X106 Y108.215 Z.6 F42000
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G1 X100.95 Y108.215 E.18809
G1 X101.327 Y107.523 E.02934
G2 X101.334 Y103.988 I-3.849 J-1.774 E.13583
G1 X100.95 Y103.285 E.02982
G1 X105.999 Y103.285 E.18805
G1 X105.613 Y103.998 E.03018
G2 X105.616 Y107.511 I3.868 J1.753 E.13489
G1 X105.971 Y108.162 E.02764
; WIPE_START
G1 X103.971 Y108.183 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X96.439 Y108.904 Z.6 F42000
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
M73 P33 R16
G1 X96.398 Y109.129 E.00852
G1 X94.596 Y109.129 E.06712
G1 X94.596 Y107.751 E.0513
G1 X94.784 Y107.689 E.00738
G1 X94.959 Y107.925 E.01094
G2 X96.382 Y108.885 I2.48 J-2.142 E.06468
; WIPE_START
G1 X96.398 Y109.129 E-.09284
G1 X94.642 Y109.129 E-.66716
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X99.115 Y106.806 Z.6 F42000
G1 Z.2
G1 E.8 F1800
; FEATURE: Outer wall
G1 F3000
M204 S500
G1 X98.948 Y107.026 E.01028
G3 X97.205 Y103.819 I-1.469 J-1.279 E.27973
G1 X97.475 Y103.799 E.01007
G3 X99.146 Y106.755 I.004 J1.948 E.15356
M204 S6000
G1 X99.481 Y107.08 F42000
; FEATURE: Inner wall
G1 F3000
M204 S500
G1 X99.294 Y107.326 E.01149
G3 X97.141 Y103.365 I-1.815 J-1.579 E.34544
G1 X97.475 Y103.341 E.01247
G3 X99.514 Y107.03 I.004 J2.406 E.19133
M204 S6000
G1 X99.919 Y107.241 F42000
G1 F3000
M204 S500
G1 X99.885 Y107.299 E.00251
G3 X97.077 Y102.911 I-2.406 J-1.553 E.42638
G1 X97.475 Y102.883 E.01486
G3 X100.078 Y106.95 I.005 J2.863 E.21395
G1 X99.948 Y107.188 E.01012
; WIPE_START
G1 X99.885 Y107.299 E-.04842
G1 X99.642 Y107.628 E-.15537
G1 X99.351 Y107.919 E-.15645
G1 X99.016 Y108.167 E-.1582
G1 X98.666 Y108.358 E-.15169
G1 X98.444 Y108.441 E-.08987
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X96.438 Y102.597 Z.6 F42000
G1 Z.2
G1 E.8 F1800
G1 F3000
M204 S500
G2 X94.784 Y103.81 I1.058 J3.176 E.07766
G1 X94.596 Y103.748 E.00736
G1 X94.596 Y102.371 E.05127
G1 X96.397 Y102.371 E.06708
G1 X96.427 Y102.538 E.0063
; WIPE_START
G1 X96.094 Y102.725 E-.14545
G1 X95.677 Y102.953 E-.18024
G1 X95.306 Y103.23 E-.17623
G1 X94.964 Y103.57 E-.18305
G1 X94.846 Y103.728 E-.07504
; WIPE_END
G1 E-.04 F1800
M204 S6000
G17
G3 Z.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z0.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X94.61 Y103.993 F42000
G1 Z.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.3533
G1 F3000
M204 S500
G1 X94.521 Y104.401 E.01055
; LINE_WIDTH: 0.328096
G1 X94.5 Y104.513 E.00265
; LINE_WIDTH: 0.28712
G1 X94.48 Y104.625 E.00227
; LINE_WIDTH: 0.246144
G1 X94.459 Y104.737 E.00189
; LINE_WIDTH: 0.203331
G1 X94.437 Y104.86 E.00163
; LINE_WIDTH: 0.162002
G1 X94.416 Y105.058 E.00193
; LINE_WIDTH: 0.122614
G1 X94.394 Y105.256 E.00129
M204 S6000
G1 X94.394 Y106.244 F42000
; LINE_WIDTH: 0.122444
G1 F3000
M204 S500
G1 X94.416 Y106.441 E.00128
; LINE_WIDTH: 0.161508
G1 X94.437 Y106.637 E.00191
; LINE_WIDTH: 0.202074
G1 X94.458 Y106.757 E.00159
; LINE_WIDTH: 0.243668
G1 X94.478 Y106.868 E.00184
; LINE_WIDTH: 0.283505
G1 X94.498 Y106.978 E.0022
; LINE_WIDTH: 0.323342
G1 X94.518 Y107.089 E.00256
; LINE_WIDTH: 0.348018
G1 X94.609 Y107.506 E.01063
M204 S6000
G1 X94.825 Y108.157 F42000
; LINE_WIDTH: 0.433625
G1 F3000
M204 S500
G1 X95.165 Y108.9 E.02603
M204 S6000
G1 X94.825 Y108.613 F42000
; LINE_WIDTH: 0.217116
G1 F3000
M204 S500
G1 X95.756 Y108.887 E.01377
M204 S6000
G1 X96.645 Y109.047 F42000
; LINE_WIDTH: 0.581764
G1 F3000
M204 S500
G2 X98.306 Y109.047 I.83 J-6.334 E.07311
M204 S6000
G1 X99.244 Y108.9 F42000
; LINE_WIDTH: 0.125438
G1 F3000
M204 S500
G1 X99.513 Y108.687 E.00231
M204 S6000
G1 X100.451 Y108.443 F42000
; LINE_WIDTH: 0.116723
G1 F3000
M204 S500
G1 X100.54 Y108.402 E.00059
G1 X100.639 Y108.249 E.0011
; WIPE_START
G1 X100.54 Y108.402 E-.49348
G1 X100.451 Y108.443 E-.26652
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X100.639 Y103.251 Z.6 F42000
G1 Z.2
G1 E.8 F1800
; LINE_WIDTH: 0.117294
G1 F3000
M204 S500
G1 X100.54 Y103.098 E.0011
G1 X100.442 Y103.057 E.00064
M204 S6000
G1 X99.507 Y102.807 F42000
; LINE_WIDTH: 0.12499
G1 F3000
M204 S500
G1 X99.244 Y102.6 E.00224
M204 S6000
G1 X98.306 Y102.453 F42000
; LINE_WIDTH: 0.581849
G1 F3000
M204 S500
G2 X96.644 Y102.453 I-.831 J6.334 E.07317
M204 S6000
G1 X95.756 Y102.614 F42000
; LINE_WIDTH: 0.216971
G1 F3000
M204 S500
G1 X94.825 Y102.887 E.01376
; WIPE_START
G1 X95.756 Y102.614 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X103.354 Y103.333 Z.6 F42000
G1 X104.776 Y103.468 Z.6
G1 Z.2
G1 E.8 F1800
; FEATURE: Bottom surface
; LINE_WIDTH: 0.50357
G1 F6300
M204 S500
G1 X105.227 Y103.92 E.02397
G1 X105.05 Y104.394 E.01901
G1 X104.33 Y103.674 E.03824
G1 X103.679 Y103.674 E.02445
G1 X104.927 Y104.923 E.06629
G2 X104.861 Y105.508 I2 J.523 E.02218
G1 X103.027 Y103.674 E.09735
G1 X102.376 Y103.674 E.02445
G1 X104.875 Y106.173 E.13266
G1 X104.893 Y106.421 E.00933
G1 X105.011 Y106.96 E.02073
G1 X101.724 Y103.674 E.17446
G1 X101.605 Y103.674 E.0045
G1 X101.688 Y103.826 E.00652
G1 X101.919 Y104.445 E.0248
G1 X101.939 Y104.54 E.00365
G1 X105.225 Y107.826 E.17444
G1 X104.574 Y107.826 E.02445
G1 X102.076 Y105.328 E.1326
G3 X102.089 Y105.993 I-2.304 J.377 E.02502
G1 X103.922 Y107.826 E.09734
G1 X103.271 Y107.826 E.02445
G1 X102.022 Y106.578 E.06628
G1 X101.9 Y107.107 E.02038
G1 X102.62 Y107.826 E.0382
G1 X101.968 Y107.826 E.02445
G1 X101.562 Y107.42 E.02157
; WIPE_START
G1 X101.968 Y107.826 E-.21834
G1 X102.62 Y107.826 E-.24755
G1 X102.072 Y107.279 E-.29411
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X106.307 Y108.241 Z.6 F42000
G1 Z.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.114492
G1 F3000
M204 S500
G1 X106.41 Y108.401 E.00111
G1 X106.5 Y108.443 E.00058
M204 S6000
G1 X107.443 Y108.693 F42000
; LINE_WIDTH: 0.12498
G1 F3000
M204 S500
G1 X107.706 Y108.9 E.00224
M204 S6000
G1 X108.646 Y109.047 F42000
; LINE_WIDTH: 0.582058
G1 F3000
M204 S500
G2 X110.306 Y109.047 I.83 J-6.324 E.07314
; WIPE_START
G1 X109.945 Y109.085 E-.16563
G1 X109.458 Y109.102 E-.2224
G1 X109.014 Y109.086 E-.20294
G1 X108.646 Y109.047 E-.16903
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X112.627 Y103.235 Z.6 F42000
G1 Z.2
G1 E.8 F1800
; LINE_WIDTH: 0.115705
G1 F3000
M204 S500
G1 X112.537 Y103.096 E.00098
G1 X112.445 Y103.057 E.0006
M204 S6000
G1 X111.513 Y102.814 F42000
; LINE_WIDTH: 0.125496
G1 F3000
M204 S500
G1 X111.244 Y102.6 E.00231
M204 S6000
G1 X110.306 Y102.453 F42000
; LINE_WIDTH: 0.581853
G1 F3000
M204 S500
G2 X108.644 Y102.453 I-.831 J6.365 E.07317
M204 S6000
G1 X107.707 Y102.6 F42000
; LINE_WIDTH: 0.125165
G1 F3000
M204 S500
G1 X107.445 Y102.806 E.00224
M204 S6000
G1 X106.499 Y103.057 F42000
; LINE_WIDTH: 0.116962
G1 F3000
M204 S500
G1 X106.408 Y103.099 E.00061
G1 X106.303 Y103.262 E.00117
; WIPE_START
G1 X106.408 Y103.099 E-.50014
G1 X106.499 Y103.057 E-.25986
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X114.123 Y103.422 Z.6 F42000
G1 X115.08 Y103.468 Z.6
G1 Z.2
G1 E.8 F1800
; FEATURE: Bottom surface
; LINE_WIDTH: 0.51024
G1 F6300
M204 S500
G1 X115.82 Y104.208 E.03985
G1 X115.82 Y104.869 E.02517
G1 X114.625 Y103.674 E.06437
G1 X113.964 Y103.674 E.02517
G1 X115.82 Y105.53 E.09996
G1 X115.82 Y106.191 E.02517
G1 X113.826 Y104.196 E.10741
G1 X113.919 Y104.447 E.01017
G1 X114.057 Y105.089 E.02502
G1 X115.82 Y106.852 E.09493
G1 X115.82 Y107.513 E.02517
G1 X114.103 Y105.795 E.09247
G1 X114.059 Y106.412 E.02353
G1 X115.82 Y108.173 E.09487
G1 X115.82 Y108.834 E.02517
G1 X113.94 Y106.955 E.10123
G1 X113.772 Y107.447 E.01982
G1 X115.82 Y109.495 E.1103
G1 X115.82 Y110.156 E.02517
G1 X113.564 Y107.9 E.12149
G1 X113.322 Y108.319 E.01842
G1 X115.82 Y110.817 E.13452
G1 X115.82 Y111.478 E.02517
G1 X113.039 Y108.697 E.14977
G3 X112.72 Y109.038 I-1.35 J-.943 E.01787
G1 X115.82 Y112.139 E.16698
G1 X115.82 Y112.8 E.02517
G1 X112.371 Y109.351 E.18573
G1 X111.995 Y109.635 E.01797
G1 X115.82 Y113.461 E.20602
G1 X115.82 Y114.121 E.02517
G1 X111.899 Y110.2 E.21118
G1 X111.899 Y110.861 E.02517
G1 X115.82 Y114.782 E.21118
G1 X115.82 Y115.443 E.02517
G1 X111.899 Y111.522 E.21118
G1 X111.899 Y112.183 E.02517
G1 X115.82 Y116.104 E.21118
G1 X115.82 Y116.765 E.02517
G1 X111.899 Y112.844 E.21118
G1 X111.899 Y113.505 E.02517
G1 X115.82 Y117.426 E.21118
G1 X115.82 Y118.087 E.02517
G1 X111.899 Y114.165 E.21118
G1 X111.899 Y114.826 E.02517
G1 X115.82 Y118.748 E.21118
G1 X115.82 Y119.326 E.02203
G1 X115.738 Y119.326 E.00314
G1 X111.899 Y115.487 E.20675
G1 X111.899 Y116.148 E.02517
G1 X115.077 Y119.326 E.17116
G1 X114.416 Y119.326 E.02517
G1 X111.899 Y116.809 E.13557
G1 X111.899 Y117.47 E.02517
G1 X113.755 Y119.326 E.09997
G1 X113.094 Y119.326 E.02517
G1 X111.899 Y118.131 E.06438
G1 X111.899 Y118.792 E.02517
G1 X112.639 Y119.532 E.03987
; WIPE_START
G1 X111.899 Y118.792 E-.39784
G1 X111.899 Y118.131 E-.25114
G1 X112.105 Y118.337 E-.11102
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X114.406 Y111.06 Z.6 F42000
G1 X117.225 Y102.143 Z.6
G1 Z.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.25758
G1 F3000
M204 S500
G1 X117.225 Y61.357 E.71342
; WIPE_START
G1 X117.225 Y63.357 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X116.418 Y60.25 Z.6 F42000
G1 Z.2
G1 E.8 F1800
; LINE_WIDTH: 0.4293
G1 F3000
M204 S500
G1 X61.832 Y60.25 E1.71866
; WIPE_START
G1 X63.832 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S6000
G1 X61.025 Y61.357 Z.6 F42000
G1 Z.2
G1 E.8 F1800
; LINE_WIDTH: 0.25758
G1 F3000
M204 S500
G1 X61.025 Y93.357 E.55974
; CHANGE_LAYER
; Z_HEIGHT: 0.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F3000
G1 X61.025 Y91.357 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 2/79
; update layer progress
M73 L2
M991 S0 P1 ;notify layer change
M106 S193.8
; open powerlost recovery
M1003 S1
; OBJECT_ID: 105
M204 S10000
G17
G3 Z.6 I-.46 J1.127 P1  F42000
G1 X99.783 Y107.166 Z.6
G1 Z.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.759 Y107.218 E.00189
G3 X97.184 Y103.059 I-2.277 J-1.467 E.36202
G3 X98.941 Y103.469 I.282 J2.767 E.06096
G3 X99.946 Y106.878 I-1.458 J2.282 E.1286
G1 X99.813 Y107.114 E.00898
M204 S10000
G1 X99.426 Y106.971 F42000
G1 F8843.478
M204 S6000
G1 X99.416 Y106.998 E.00093
G3 X97.213 Y103.465 I-1.934 J-1.247 E.30704
M73 P34 R16
G3 X98.432 Y103.655 I.274 J2.252 E.04145
G3 X99.546 Y106.768 I-.95 J2.096 E.12237
G1 X99.457 Y106.92 E.00585
M204 S250
G1 X99.087 Y106.786 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.24 Y103.856 I-1.603 J-1.036 E.23522
G3 X97.747 Y103.859 I.244 J1.764 E.01561
G3 X99.118 Y106.735 I-.263 J1.89 E.11584
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.12638
G1 X98.726 Y107.194 E-.1036
G1 X98.508 Y107.357 E-.10358
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10356
G1 X97.747 Y107.641 E-.10359
G1 X97.475 Y107.661 E-.10362
G1 X97.443 Y107.658 E-.01208
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z.8 F42000
G1 Z.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X95.164 Y103.084 E.01902
G1 X94.798 Y103.45 E.01718
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.164 Y103.084 E-.22612
G1 X94.798 Y103.45 E-.19677
G1 X94.798 Y102.573 E-.33322
G1 X94.808 Y102.573 E-.00388
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z.8 F42000
G1 Z.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.057 Y108.308 E.01213
G1 X95.165 Y108.416 E.00507
G1 X95.575 Y108.724 E.01701
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29243
G1 X94.798 Y108.05 E-.33325
G1 X94.905 Y108.156 E-.05711
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z.8 F42000
G1 X106.69 Y108.52 Z.8
G1 Z.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21178
G1 X100.786 Y107.878 E.02659
G1 X101.056 Y107.385 E.01865
G2 X100.786 Y103.622 I-3.664 J-1.629 E.13028
G1 X100.306 Y102.98 E.02659
G1 X106.645 Y102.98 E.21028
G1 X106.166 Y103.618 E.02645
G1 X105.903 Y104.099 E.01819
G2 X106.648 Y108.477 I3.577 J1.643 E.15651
; WIPE_START
G1 X104.648 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.623 Y108.76 Z.8 F42000
G1 Z.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.567 Y108.927 E.00584
G1 X99.382 Y108.927 E.27152
G1 X99.327 Y108.76 E.00584
G2 X100.141 Y103.44 I-1.89 J-3.012 E.2025
G2 X99.327 Y102.74 I-2.84 J2.485 E.03573
G1 X99.382 Y102.573 E.00584
G1 X107.571 Y102.573 E.27163
G1 X107.626 Y102.742 E.00588
G2 X107.162 Y108.414 I1.875 J3.008 E.21915
G1 X107.575 Y108.724 E.01712
; WIPE_START
G1 X107.567 Y108.927 E-.07719
G1 X105.77 Y108.927 E-.68281
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.845 Y108.547 Z.8 F42000
G1 Z.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.768 Y108.59 E.00294
G3 X109.364 Y102.638 I-1.287 J-2.838 E.36483
G3 X111.835 Y103.709 I.101 J3.153 E.09229
G3 X111.159 Y108.378 I-2.353 J2.043 E.1775
G1 X110.898 Y108.519 E.00984
M204 S10000
G1 X110.651 Y108.19 F42000
G1 F8843.478
M204 S6000
G1 X110.596 Y108.212 E.00197
G3 X109.39 Y103.044 I-1.121 J-2.463 E.31752
G3 X110.866 Y103.428 I.07 J2.763 E.05124
G3 X110.935 Y108.028 I-1.391 J2.322 E.18243
G1 X110.703 Y108.16 E.00886
M204 S10000
G1 X110.456 Y107.832 F42000
G1 F8843.478
M204 S6000
G1 X110.43 Y107.847 E.00101
G3 X109.416 Y103.451 I-.947 J-2.097 E.26998
G3 X110.434 Y103.656 I.075 J2.256 E.03476
G3 X110.719 Y107.691 I-.952 J2.095 E.16393
G1 X110.509 Y107.804 E.00791
M204 S250
G1 X110.269 Y107.488 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.266 Y107.487 E.00008
G3 X109.441 Y103.842 I-.784 J-1.739 E.20771
G3 X110.015 Y103.918 I-.017 J2.347 E.01785
G3 X110.506 Y107.358 I-.534 J1.831 E.13429
G1 X110.321 Y107.459 E.00646
; WIPE_START
M204 S6000
G1 X110.266 Y107.487 E-.02364
G1 X110.011 Y107.584 E-.10349
G1 X109.78 Y107.634 E-.08993
G1 X109.473 Y107.661 E-.11719
G1 X109.201 Y107.641 E-.10354
G1 X108.933 Y107.582 E-.10412
G1 X108.679 Y107.487 E-.10307
G1 X108.44 Y107.356 E-.1036
G1 X108.416 Y107.338 E-.01143
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.306 Y102.98 Z.8 F42000
G1 Z.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.13928
G1 X116.551 Y103.305 E.01088
G1 X116.551 Y120.02 E.55446
G1 X111.205 Y120.02 E.17734
G1 X111.205 Y109.278 E.35632
G2 X112.688 Y103.491 I-1.741 J-3.53 E.22502
G1 X112.342 Y103.028 E.01915
; WIPE_START
G1 X114.342 Y103.005 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.383 Y102.573 Z.8 F42000
G1 Z.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18308
G1 X116.902 Y102.88 E.01018
G1 X116.958 Y103.276 E.01326
G1 X116.958 Y120.427 E.56893
G1 X110.798 Y120.427 E.20435
G1 X110.798 Y109.012 E.37864
G1 X110.937 Y108.961 E.0049
G2 X111.788 Y103.086 I-1.477 J-3.213 E.23365
G1 X111.327 Y102.74 E.01914
G1 X111.364 Y102.63 E.00385
; WIPE_START
G1 X113.364 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.733 Y102.431 Z.8 F42000
G1 X94.391 Y102.166 Z.8
G1 Z.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.366 Y103.247 E.01326
G1 X117.366 Y120.834 E.58339
G1 X110.391 Y120.834 E.23135
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.962 E.07869
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00427
G2 X94.637 Y104.454 I2.834 J-1.296 E.5609
G1 X94.592 Y104.575 E.00428
G1 X94.391 Y104.539 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z.8 F42000
G1 X61.755 Y60.52 Z.8
G1 Z.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X117.773 Y103.218 E.01326
G1 X117.773 Y121.241 E.59786
G1 X109.984 Y121.241 E.25836
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.18 Y103.189 E.01326
G1 X118.18 Y121.648 E.61233
G1 X109.577 Y121.648 E.28537
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.572 Y103.161 E.01228
G1 X118.572 Y122.04 E.58011
G1 X109.185 Y122.04 E.28843
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z0.8
G1 X0 Y90 F18000 ; move to safe pos
M73 P35 R16
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z.8 F42000
G1 X61.959 Y60.25 Z.8
G1 Z.4
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z.8 F42000
G1 Z.4
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.065 Y103.04 Z.8 F42000
G1 Z.4
G1 E.8 F1800
; LINE_WIDTH: 0.10785
G1 F15000
M204 S6000
G1 X111.945 Y102.902 E.00096
; LINE_WIDTH: 0.133766
G1 X111.82 Y102.777 E.00131
M204 S10000
G1 X111.155 Y102.613 F42000
; LINE_WIDTH: 0.427226
G1 F9367.546
M204 S6000
G2 X110.923 Y102.555 I-.945 J3.276 E.00748
; LINE_WIDTH: 0.391309
G1 F10333.297
G1 X110.805 Y102.533 E.00341
; LINE_WIDTH: 0.348483
G1 F11781.527
G1 X110.687 Y102.512 E.00299
; LINE_WIDTH: 0.305658
G1 F13701.87
M73 P35 R15
G1 X110.568 Y102.49 E.00257
; LINE_WIDTH: 0.260367
G1 F15000
G1 X110.436 Y102.467 E.00238
; LINE_WIDTH: 0.220275
G1 X110.278 Y102.45 E.0023
; LINE_WIDTH: 0.186069
G1 X110.12 Y102.433 E.00186
; LINE_WIDTH: 0.151169
G1 X109.955 Y102.415 E.00146
; LINE_WIDTH: 0.116762
G1 X109.487 Y102.398 E.00282
G2 X108.995 Y102.415 I-.013 J6.794 E.00296
; LINE_WIDTH: 0.150653
G1 X108.838 Y102.432 E.00139
; LINE_WIDTH: 0.184376
G1 X108.68 Y102.449 E.00183
; LINE_WIDTH: 0.219628
G1 X108.508 Y102.468 E.00249
; LINE_WIDTH: 0.260274
G1 X108.39 Y102.489 E.00213
; LINE_WIDTH: 0.302933
G1 F13845.5
G1 X108.271 Y102.51 E.00255
; LINE_WIDTH: 0.345592
G1 F11894.087
G1 X108.152 Y102.532 E.00297
; LINE_WIDTH: 0.388251
G1 F10424.797
G1 X108.034 Y102.553 E.00339
; LINE_WIDTH: 0.425176
G1 F9417.786
G2 X107.798 Y102.612 I.726 J3.403 E.00759
M204 S10000
G1 X107.13 Y102.777 F42000
; LINE_WIDTH: 0.133147
G1 F15000
M204 S6000
G1 X107.007 Y102.901 E.00129
; LINE_WIDTH: 0.107876
G1 X106.888 Y103.037 E.00096
; WIPE_START
G1 X107.007 Y102.901 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X101.089 Y103.372 Z.8 F42000
G1 Z.4
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X101.406 Y103.94 E.01997
G3 X101.632 Y106.957 I-4.113 J1.824 E.0948
G3 X101.089 Y108.128 I-4.072 J-1.175 E.03981
G1 X105.861 Y108.128 E.14663
G1 X105.541 Y107.556 E.02014
G3 X105.32 Y104.54 I4.114 J-1.819 E.09477
G3 X105.844 Y103.394 I4.233 J1.246 E.03883
G1 X105.833 Y103.372 E.00076
G1 X101.149 Y103.372 E.14392
M204 S10000
G1 X101.732 Y103.75 F42000
G1 F9547.299
M204 S6000
G1 X101.977 Y104.386 E.02096
G1 X102.126 Y105.041 E.02062
G1 X102.179 Y105.702 E.0204
G1 X102.141 Y106.318 E.01896
G1 X102 Y107.037 E.0225
G2 X101.743 Y107.751 I12.219 J4.795 E.02331
G1 X105.218 Y107.751 E.10677
G1 X104.971 Y107.11 E.0211
G1 X104.822 Y106.438 E.02114
G3 X104.951 Y104.459 I5.225 J-.653 E.06131
G1 X105.218 Y103.75 E.02329
G1 X101.792 Y103.75 E.10527
M204 S10000
G1 X102.283 Y104.127 F42000
G1 F9547.299
M204 S6000
G1 X102.494 Y104.96 E.02643
G1 X102.555 Y105.676 E.02205
G1 X102.518 Y106.345 E.02061
G1 X102.368 Y107.117 E.02415
G1 X102.283 Y107.373 E.00831
G1 X104.667 Y107.373 E.07326
G1 X104.453 Y106.517 E.02713
G1 X104.395 Y105.818 E.02153
G1 X104.433 Y105.156 E.02038
G1 X104.583 Y104.378 E.02434
G1 X104.667 Y104.127 E.00816
G1 X102.343 Y104.127 E.07142
M204 S10000
G1 X102.781 Y104.504 F42000
G1 F9547.299
M204 S6000
G3 X102.781 Y106.996 I-5.099 J1.246 E.07733
G1 X104.17 Y106.996 E.04269
G3 X104.17 Y104.504 I5.103 J-1.247 E.07733
G1 X102.841 Y104.504 E.04083
M204 S10000
G1 X103.253 Y104.889 F42000
; LINE_WIDTH: 0.423878
G1 F9449.861
M204 S6000
G3 X103.252 Y106.611 I-9.54 J.86 E.05351
G1 X103.698 Y106.611 E.01384
G3 X103.698 Y104.889 I9.464 J-.865 E.05351
G1 X103.313 Y104.889 E.01195
; WIPE_START
G1 X103.698 Y104.889 E-.1463
G1 X103.672 Y105.101 E-.08096
G1 X103.653 Y105.871 E-.29259
G1 X103.692 Y106.501 E-.24015
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z.8 F42000
G1 Z.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108298
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134093
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.42643
G1 F9386.981
M204 S6000
G2 X98.92 Y102.554 I-.955 J3.311 E.00755
; LINE_WIDTH: 0.389895
G1 F10375.413
G1 X98.802 Y102.533 E.00341
; LINE_WIDTH: 0.347119
G1 F11834.371
G1 X98.683 Y102.511 E.00299
; LINE_WIDTH: 0.304344
G1 F13770.774
G1 X98.565 Y102.49 E.00257
; LINE_WIDTH: 0.259122
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219174
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185169
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150478
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.116325
G1 X97.473 Y102.398 E.00286
G2 X96.993 Y102.415 I.005 J6.813 E.00287
; LINE_WIDTH: 0.151064
G1 X96.835 Y102.432 E.0014
; LINE_WIDTH: 0.185103
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.220685
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.261558
G1 X96.386 Y102.49 E.00215
; LINE_WIDTH: 0.30433
G1 F13771.466
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347102
G1 F11835.017
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.389874
G1 F10376.015
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426415
G1 F9387.36
G2 X95.796 Y102.613 I.723 J3.382 E.00755
M204 S10000
G1 X94.732 Y103.84 F42000
; LINE_WIDTH: 0.106651
G1 F15000
M204 S6000
G1 X94.649 Y103.936 E.00067
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497406
G1 F7921.044
M204 S6000
G1 X94.419 Y105.024 E.00998
; LINE_WIDTH: 0.463221
G1 F8565.29
G2 X94.389 Y105.321 I4.136 J.58 E.01022
; LINE_WIDTH: 0.429914
G1 F9302.468
G2 X94.391 Y106.208 I8.943 J.423 E.028
; LINE_WIDTH: 0.465008
G1 F8529.039
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.49743
G1 F7920.633
G1 X94.448 Y106.744 E.00999
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.10662
G1 F15000
M204 S6000
G2 X94.649 Y107.564 I.127 J.005 E.00052
G1 X94.732 Y107.66 E.00066
M204 S10000
G1 X95.796 Y108.887 F42000
; LINE_WIDTH: 0.426422
G1 F9387.181
M204 S6000
G2 X96.03 Y108.946 I.944 J-3.262 E.00755
; LINE_WIDTH: 0.389897
G1 F10375.337
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.347127
G1 F11834.081
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304356
G1 F13770.116
G1 X96.385 Y109.01 E.00257
; LINE_WIDTH: 0.261586
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.22074
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185188
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.151183
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.116375
G2 X97.473 Y109.102 I.487 J-6.82 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.150503
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185193
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219198
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259142
G1 X98.564 Y109.01 E.00237
; LINE_WIDTH: 0.304339
G1 F13771.022
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.347091
G1 F11835.444
G1 X98.802 Y108.968 E.00298
; LINE_WIDTH: 0.389844
G1 F10376.921
G1 X98.92 Y108.946 E.0034
; LINE_WIDTH: 0.426395
G1 F9387.851
G2 X99.154 Y108.887 I-.723 J-3.382 E.00755
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.134083
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.108278
G1 X100.065 Y108.46 E.001
; WIPE_START
G1 X99.942 Y108.601 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.57 Y108.879 Z.8 F42000
G1 X107.795 Y108.887 Z.8
G1 Z.4
G1 E.8 F1800
; LINE_WIDTH: 0.427429
G1 F9362.59
M204 S6000
G2 X108.026 Y108.945 I.939 J-3.246 E.00746
; LINE_WIDTH: 0.392035
G1 F10311.8
G1 X108.142 Y108.966 E.00336
; LINE_WIDTH: 0.350002
G1 F11723.257
G1 X108.258 Y108.987 E.00295
; LINE_WIDTH: 0.307969
G1 F13582.388
G1 X108.374 Y109.008 E.00255
; LINE_WIDTH: 0.265937
G1 F15000
G1 X108.49 Y109.029 E.00214
; LINE_WIDTH: 0.226759
G1 X108.642 Y109.047 E.00229
; LINE_WIDTH: 0.190659
G1 X108.816 Y109.066 E.00211
; LINE_WIDTH: 0.1533
G1 X108.989 Y109.084 E.00157
; LINE_WIDTH: 0.116216
G2 X109.469 Y109.102 I.493 J-6.876 E.00287
G1 X109.938 Y109.086 E.0028
; LINE_WIDTH: 0.149339
G1 X110.105 Y109.068 E.00146
; LINE_WIDTH: 0.184123
G1 X110.267 Y109.051 E.00187
; LINE_WIDTH: 0.218255
G1 X110.429 Y109.034 E.00232
; LINE_WIDTH: 0.246658
G1 X110.595 Y109.005 E.0028
; WIPE_START
G1 X110.429 Y109.034 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.354 Y116.084 Z.8 F42000
G1 X113.878 Y117.347 Z.8
G1 Z.4
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.45708
G1 F8692.293
M204 S6000
G1 X113.878 Y110.735 E.22314
M204 S10000
G1 X113.483 Y110.492 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X113.483 Y117.742 E.22276
G1 X114.274 Y117.742 E.02431
G1 X114.274 Y109.69 E.24741
G1 X113.528 Y110.453 E.03278
M204 S10000
G1 X113.106 Y110.31 F42000
G1 F9547.299
M204 S6000
G1 X113.106 Y118.119 E.23994
G1 X114.651 Y118.119 E.04748
G1 X114.651 Y108.428 E.29777
G3 X113.366 Y110.095 I-5.378 J-2.817 E.06501
G1 X113.152 Y110.272 E.00853
M204 S10000
G1 X114.95 Y106.585 F42000
; LINE_WIDTH: 0.562025
G1 F6935.014
M204 S6000
G1 X114.965 Y106.219 E.01547
; LINE_WIDTH: 0.535405
G1 F7309.873
G2 X114.96 Y105.083 I-8.438 J-.53 E.04563
; LINE_WIDTH: 0.578405
G1 F6722.878
G1 X114.941 Y104.879 E.00895
; LINE_WIDTH: 0.620895
G1 F6228.644
G1 X114.922 Y104.674 E.00966
M204 S10000
G1 X114.95 Y106.585 F42000
; LINE_WIDTH: 0.557427
G1 F6997
M204 S6000
G1 X114.895 Y106.743 E.00705
; LINE_WIDTH: 0.518159
G1 F7575.14
G1 X114.84 Y106.902 E.00651
; LINE_WIDTH: 0.478892
G1 F8257.425
G1 X114.785 Y107.061 E.00597
; LINE_WIDTH: 0.420119
G1 F9544.044
G3 X114.475 Y107.937 I-55.476 J-19.122 E.02855
G1 X114.113 Y108.626 E.02393
G1 X113.657 Y109.256 E.02391
G1 X113.1 Y109.828 E.02451
G1 X112.729 Y110.121 E.01456
G1 X112.729 Y118.496 E.25742
G1 X115.028 Y118.496 E.07068
G1 X115.028 Y107.253 E.34559
; LINE_WIDTH: 0.442039
G1 F9019.881
G1 X115.006 Y107.051 E.0066
; LINE_WIDTH: 0.486135
G1 F8122.469
G1 X114.984 Y106.849 E.00733
; LINE_WIDTH: 0.530232
G1 F7387.469
G1 X114.962 Y106.647 E.00806
; LINE_WIDTH: 0.56467
G1 F6899.857
G1 X114.961 Y106.643 E.00017
M204 S10000
G1 X114.283 Y104.127 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G3 X114.122 Y107.805 I-4.931 J1.627 E.11564
G1 X113.782 Y108.445 E.02227
G1 X113.355 Y109.03 E.02225
G1 X112.835 Y109.56 E.02281
G1 X112.352 Y109.932 E.01875
G1 X112.352 Y118.873 E.27473
G1 X115.405 Y118.873 E.09383
G1 X115.405 Y104.127 E.45312
G1 X114.343 Y104.127 E.03264
M204 S10000
G1 X113.732 Y103.749 F42000
G1 F9547.299
M204 S6000
G1 X113.978 Y104.39 E.02109
G1 X114.128 Y105.063 E.02118
G1 X114.179 Y105.715 E.02011
G1 X114.136 Y106.384 E.02059
G1 X113.993 Y107.057 E.02113
G1 X113.769 Y107.672 E.02014
G1 X113.451 Y108.264 E.02062
G1 X113.053 Y108.804 E.0206
G1 X112.569 Y109.292 E.02113
G3 X111.974 Y109.741 I-7.541 J-9.38 E.0229
G1 X111.974 Y119.251 E.2922
G1 X115.782 Y119.251 E.117
G1 X115.782 Y103.749 E.47629
G1 X113.792 Y103.749 E.06116
M204 S10000
G1 X113.086 Y103.372 F42000
G1 F9547.299
M204 S6000
G1 X113.409 Y103.944 E.02017
G3 X113.803 Y105.742 I-4.529 J1.936 E.05687
G3 X113.416 Y107.54 I-4.916 J-.118 E.05687
G3 X111.597 Y109.511 I-4.035 J-1.898 E.08368
G1 X111.597 Y119.628 E.31084
G1 X116.159 Y119.628 E.14017
G1 X116.159 Y103.372 E.49946
G1 X113.146 Y103.372 E.09258
; CHANGE_LAYER
; Z_HEIGHT: 0.6
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X115.146 Y103.372 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 3/79
; update layer progress
M73 L3
M991 S0 P2 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z.8 I-.298 J-1.18 P1  F42000
G1 X99.722 Y107.261 Z.8
G1 Z.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.526 Y107.528 E.01097
G3 X97.198 Y103.058 I-2.045 J-1.776 E.34967
G3 X99.251 Y103.701 I.289 J2.675 E.07339
G3 X99.761 Y107.215 I-1.769 J2.051 E.12848
M204 S10000
G1 X99.396 Y107.017 F42000
G1 F8843.478
M204 S6000
G1 X99.218 Y107.261 E.01
G3 X97.227 Y103.464 I-1.735 J-1.51 E.29643
G3 X98.432 Y103.655 I.262 J2.248 E.04096
G3 X99.433 Y106.971 I-.949 J2.096 E.1301
M204 S250
G1 X99.086 Y106.785 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.255 Y103.855 I-1.603 J-1.035 E.23571
G3 X98.013 Y103.917 I.213 J2.073 E.0235
G3 X99.118 Y106.734 I-.531 J1.833 E.10737
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.12638
G1 X98.726 Y107.194 E-.1036
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.10359
G1 X98.013 Y107.583 E-.10359
G1 X97.747 Y107.641 E-.10357
G1 X97.475 Y107.661 E-.1036
G1 X97.443 Y107.658 E-.0121
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z1 F42000
G1 Z.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X95.165 Y103.084 E.01901
G1 X94.798 Y103.45 E.01719
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.165 Y103.084 E-.22599
G1 X94.798 Y103.45 E-.19691
G1 X94.798 Y102.573 E-.33323
G1 X94.808 Y102.573 E-.00387
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z1 F42000
G1 Z.6
G1 E.8 F1800
M73 P36 R15
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.046 Y108.298 E.01162
G1 X95.165 Y108.416 E.00556
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07721
G1 X94.798 Y108.927 E-.29242
G1 X94.798 Y108.05 E-.33323
G1 X94.905 Y108.156 E-.05714
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z1 F42000
G1 X106.691 Y108.52 Z1
G1 Z.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21179
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.312 J-2.128 E.14915
G1 X100.306 Y102.98 E.02659
G1 X106.645 Y102.98 E.21029
G1 X106.168 Y103.616 E.02636
G1 X105.904 Y104.097 E.01821
G2 X106.649 Y108.477 I3.577 J1.645 E.15659
; WIPE_START
G1 X104.649 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.623 Y108.76 Z1 F42000
G1 Z.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.567 Y108.927 E.00584
G1 X99.382 Y108.927 E.27151
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18578
G2 X99.327 Y102.74 I-3.356 J2.283 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.571 Y102.573 E.27164
G1 X107.626 Y102.742 E.00588
G2 X107.161 Y108.413 I1.875 J3.008 E.21909
G1 X107.575 Y108.724 E.01717
; WIPE_START
G1 X107.567 Y108.927 E-.07717
G1 X105.77 Y108.927 E-.68283
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.684 Y108.621 Z1 F42000
G1 Z.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.349 Y108.745 E.01184
G3 X109.351 Y102.639 I-.868 J-2.993 E.34953
G3 X111.836 Y103.711 I.114 J3.153 E.09278
G3 X110.766 Y108.591 I-2.354 J2.041 E.1923
G1 X110.74 Y108.6 E.00089
M204 S10000
G1 X110.542 Y108.239 F42000
G1 F8843.478
M204 S6000
G1 X110.233 Y108.347 E.01087
G3 X109.377 Y103.045 I-.758 J-2.598 E.30422
G3 X110.855 Y103.421 I.086 J2.752 E.05126
G3 X110.596 Y108.212 I-1.38 J2.328 E.19565
M204 S10000
G1 X110.401 Y107.857 F42000
G1 F8843.478
M204 S6000
G1 X110.12 Y107.962 E.00993
G3 X109.403 Y103.451 I-.637 J-2.211 E.25853
G3 X110.436 Y103.656 I.09 J2.25 E.03526
G3 X110.457 Y107.836 I-.952 J2.095 E.17387
M204 S250
G1 X110.265 Y107.49 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.009 Y107.582 E.00835
G3 X109.428 Y103.843 I-.526 J-1.833 E.19877
G3 X110.017 Y103.918 I.011 J2.257 E.01831
G3 X110.318 Y107.464 I-.534 J1.831 E.14093
; WIPE_START
M204 S6000
G1 X110.009 Y107.582 E-.1258
G1 X109.793 Y107.631 E-.0841
G1 X109.471 Y107.661 E-.12294
G1 X109.2 Y107.641 E-.10352
G1 X108.932 Y107.582 E-.1041
G1 X108.678 Y107.486 E-.10313
G1 X108.439 Y107.355 E-.10357
G1 X108.412 Y107.335 E-.01283
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.306 Y102.98 Z1 F42000
G1 Z.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.13928
G1 X116.589 Y103.569 E.01972
G1 X116.589 Y120.02 E.54571
G1 X111.205 Y120.02 E.17859
G1 X111.205 Y109.278 E.35632
G2 X112.178 Y108.599 I-1.864 J-3.708 E.0395
G2 X112.68 Y103.48 I-2.71 J-2.85 E.18596
G1 X112.342 Y103.028 E.01873
; WIPE_START
G1 X114.342 Y103.005 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.383 Y102.573 Z1 F42000
G1 Z.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18307
G1 X116.902 Y102.88 E.01018
G1 X116.996 Y103.54 E.0221
G1 X116.996 Y120.427 E.56018
G1 X110.798 Y120.427 E.2056
G1 X110.798 Y109.012 E.37863
G1 X110.934 Y108.962 E.00481
G2 X111.791 Y103.088 I-1.475 J-3.214 E.23364
G1 X111.327 Y102.74 E.01922
G1 X111.364 Y102.63 E.00385
; WIPE_START
G1 X113.364 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.734 Y102.431 Z1 F42000
G1 X94.391 Y102.166 Z1
G1 Z.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.403 Y103.511 E.0221
G1 X117.403 Y120.834 E.57464
G1 X110.391 Y120.834 E.23261
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.961 E.0787
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00428
G2 X94.637 Y104.454 I2.833 J-1.296 E.56056
G1 X94.592 Y104.575 E.00428
G1 X94.391 Y104.538 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z1 F42000
G1 X61.755 Y60.52 Z1
G1 Z.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X117.81 Y103.482 E.0221
G1 X117.81 Y121.241 E.58911
G1 X109.984 Y121.241 E.25961
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.218 Y103.452 E.0221
G1 X118.218 Y121.648 E.60358
G1 X109.577 Y121.648 E.28662
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.61 Y103.424 E.02047
G1 X118.61 Y121.93 E.56861
G1 X118.573 Y122.04 E.00357
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z1 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z1
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    
      M400
      G90
      M83
      M204 S5000
      G0 Z2 F4000
      G0 X187 Y178 F20000
      G39 S1 X187 Y178
      G0 Z2 F4000
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
        M623
    
    M623
M623
; SKIPPABLE_END




G1 Z1.000
G1 X61.025 Y61.537 F42000
G1 Z.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z1 F42000
G1 X61.959 Y60.25 Z1
G1 Z.6
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
M73 P37 R15
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z1 F42000
G1 Z.6
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.065 Y103.04 Z1 F42000
G1 Z.6
G1 E.8 F1800
; LINE_WIDTH: 0.107554
G1 F15000
M204 S6000
G1 X111.947 Y102.904 E.00094
; LINE_WIDTH: 0.133569
G1 X111.82 Y102.777 E.00133
M204 S10000
G1 X111.155 Y102.613 F42000
; LINE_WIDTH: 0.427746
G1 F9354.89
M204 S6000
G2 X110.925 Y102.555 I-.946 J3.285 E.00743
; LINE_WIDTH: 0.392199
G1 F10306.95
G1 X110.807 Y102.534 E.00342
; LINE_WIDTH: 0.349348
G1 F11748.281
G1 X110.689 Y102.512 E.003
; LINE_WIDTH: 0.306497
G1 F13658.265
G1 X110.571 Y102.491 E.00258
; LINE_WIDTH: 0.261161
G1 F15000
G1 X110.439 Y102.467 E.00239
; LINE_WIDTH: 0.220968
G1 X110.281 Y102.45 E.00231
; LINE_WIDTH: 0.186653
G1 X110.123 Y102.433 E.00186
; LINE_WIDTH: 0.151638
G1 X109.958 Y102.415 E.00147
; LINE_WIDTH: 0.116803
G1 X109.489 Y102.398 E.00283
G2 X108.997 Y102.415 I-.007 J6.994 E.00296
; LINE_WIDTH: 0.150382
G1 X108.84 Y102.432 E.00139
; LINE_WIDTH: 0.183917
G1 X108.682 Y102.449 E.00182
; LINE_WIDTH: 0.218967
G1 X108.511 Y102.467 E.00247
; LINE_WIDTH: 0.259443
G1 X108.393 Y102.489 E.00213
; LINE_WIDTH: 0.301985
G1 F13896.132
G1 X108.274 Y102.51 E.00254
; LINE_WIDTH: 0.344527
G1 F11936.065
G1 X108.155 Y102.531 E.00296
; LINE_WIDTH: 0.387069
G1 F10460.586
G1 X108.037 Y102.552 E.00338
; LINE_WIDTH: 0.42451
G1 F9434.206
G2 X107.798 Y102.612 I.731 J3.437 E.00766
M204 S10000
G1 X107.131 Y102.777 F42000
; LINE_WIDTH: 0.120086
G1 F15000
M204 S6000
G1 X106.89 Y103.035 E.00222
; WIPE_START
G1 X107.131 Y102.777 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X101.089 Y103.372 Z1 F42000
G1 Z.6
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X101.406 Y103.94 E.01997
G3 X101.632 Y106.957 I-4.113 J1.824 E.0948
G3 X101.089 Y108.128 I-4.069 J-1.174 E.03981
G1 X105.862 Y108.128 E.14664
G1 X105.54 Y107.552 E.02025
G3 X105.32 Y104.537 I4.116 J-1.815 E.09474
G3 X105.846 Y103.392 I4.223 J1.244 E.03885
G1 X105.229 Y103.372 E.01897
G1 X101.149 Y103.372 E.12535
M204 S10000
G1 X101.732 Y103.749 F42000
G1 F9547.299
M204 S6000
G1 X101.977 Y104.386 E.02095
G1 X102.126 Y105.041 E.02063
G3 X102 Y107.037 I-5.264 J.671 E.06183
G2 X101.743 Y107.751 I15.014 J5.809 E.02331
G1 X105.218 Y107.751 E.10679
G1 X104.971 Y107.107 E.02119
G1 X104.822 Y106.436 E.02111
G3 X104.952 Y104.456 I5.239 J-.65 E.06134
G1 X105.218 Y103.75 E.0232
G1 X101.792 Y103.749 E.10527
M204 S10000
G1 X102.283 Y104.127 F42000
G1 F9547.299
M204 S6000
G1 X102.494 Y104.96 E.02643
G1 X102.554 Y105.67 E.0219
G1 X102.518 Y106.345 E.02077
G1 X102.368 Y107.117 E.02415
G1 X102.283 Y107.373 E.00831
G1 X104.667 Y107.373 E.07326
G1 X104.453 Y106.515 E.02719
G1 X104.395 Y105.819 E.02145
G1 X104.433 Y105.157 E.02037
G1 X104.584 Y104.375 E.02447
G1 X104.667 Y104.127 E.00806
G1 X102.343 Y104.127 E.07142
M204 S10000
G1 X102.781 Y104.504 F42000
G1 F9547.299
M204 S6000
G3 X102.781 Y106.996 I-5.099 J1.246 E.07733
G1 X104.17 Y106.996 E.04269
G3 X104.17 Y104.504 I5.109 J-1.247 E.07733
G1 X102.841 Y104.504 E.04084
M204 S10000
G1 X103.253 Y104.889 F42000
; LINE_WIDTH: 0.423946
G1 F9448.179
M204 S6000
G3 X103.252 Y106.611 I-9.596 J.859 E.05352
G1 X103.698 Y106.611 E.01385
G3 X103.697 Y104.889 I9.51 J-.865 E.05352
G1 X103.313 Y104.889 E.01195
; WIPE_START
G1 X103.697 Y104.889 E-.14627
G1 X103.672 Y105.101 E-.08103
G1 X103.653 Y105.871 E-.29252
G1 X103.692 Y106.502 E-.24018
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z1 F42000
G1 Z.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108304
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134115
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.426427
G1 F9387.066
M204 S6000
G2 X98.92 Y102.554 I-.938 J3.239 E.00755
; LINE_WIDTH: 0.389892
G1 F10375.488
G1 X98.802 Y102.533 E.00341
; LINE_WIDTH: 0.347112
G1 F11834.663
G1 X98.683 Y102.511 E.00299
; LINE_WIDTH: 0.304331
G1 F13771.433
G1 X98.565 Y102.49 E.00257
; LINE_WIDTH: 0.259105
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219161
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185169
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150491
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.116355
G1 X97.473 Y102.398 E.00286
G2 X96.992 Y102.415 I-.004 J6.548 E.00288
; LINE_WIDTH: 0.151143
G1 X96.834 Y102.432 E.0014
; LINE_WIDTH: 0.185134
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.22067
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.261544
G1 X96.386 Y102.49 E.00215
; LINE_WIDTH: 0.304349
G1 F13770.494
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347153
G1 F11833.031
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.389958
G1 F10373.513
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426474
G1 F9385.92
G2 X95.796 Y102.613 I.721 J3.371 E.00755
M204 S10000
G1 X94.732 Y103.84 F42000
; LINE_WIDTH: 0.106639
G1 F15000
M204 S6000
G1 X94.649 Y103.936 E.00066
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497416
G1 F7920.872
M204 S6000
G1 X94.419 Y105.024 E.00999
; LINE_WIDTH: 0.463238
G1 F8564.942
G2 X94.389 Y105.321 I4.147 J.581 E.01023
; LINE_WIDTH: 0.42991
G1 F9302.579
G2 X94.391 Y106.208 I8.941 J.423 E.028
; LINE_WIDTH: 0.464977
G1 F8529.667
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.497406
G1 F7921.046
G1 X94.448 Y106.744 E.00998
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.106654
G1 F15000
M204 S6000
G2 X94.649 Y107.564 I.127 J.005 E.00052
G1 X94.732 Y107.66 E.00066
M204 S10000
G1 X95.796 Y108.887 F42000
; LINE_WIDTH: 0.426421
G1 F9387.215
M204 S6000
G2 X96.03 Y108.946 I.957 J-3.319 E.00755
; LINE_WIDTH: 0.389874
G1 F10376.011
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.34711
G1 F11834.705
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304346
G1 F13770.623
G1 X96.385 Y109.01 E.00257
; LINE_WIDTH: 0.261582
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.22074
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185198
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.1512
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.11638
G2 X97.473 Y109.102 I.477 J-6.534 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.150494
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185163
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219148
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259125
G1 X98.565 Y109.01 E.00237
; LINE_WIDTH: 0.304395
G1 F13768.066
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.347213
G1 F11830.712
G1 X98.802 Y108.967 E.00299
; LINE_WIDTH: 0.390031
G1 F10371.324
G1 X98.92 Y108.946 E.00341
; LINE_WIDTH: 0.426525
G1 F9384.652
G2 X99.154 Y108.887 I-.705 J-3.303 E.00754
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.134108
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.108278
G1 X100.065 Y108.46 E.001
; WIPE_START
G1 X99.942 Y108.601 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.57 Y108.879 Z1 F42000
G1 X107.795 Y108.887 Z1
G1 Z.6
G1 E.8 F1800
; LINE_WIDTH: 0.428136
G1 F9345.413
M204 S6000
G2 X108.023 Y108.945 I.937 J-3.24 E.00738
; LINE_WIDTH: 0.393216
G1 F10277.034
G1 X108.139 Y108.966 E.00337
; LINE_WIDTH: 0.351017
G1 F11684.637
G1 X108.255 Y108.987 E.00297
; LINE_WIDTH: 0.308818
G1 F13539.02
G1 X108.372 Y109.008 E.00256
; LINE_WIDTH: 0.26662
G1 F15000
G1 X108.488 Y109.029 E.00215
; LINE_WIDTH: 0.225445
G1 X108.657 Y109.049 E.00252
; LINE_WIDTH: 0.188324
G1 X108.822 Y109.066 E.00198
; LINE_WIDTH: 0.152776
G1 X108.987 Y109.084 E.00148
; LINE_WIDTH: 0.11623
G2 X109.466 Y109.102 I.498 J-6.935 E.00286
G1 X109.936 Y109.086 E.00281
; LINE_WIDTH: 0.148989
G1 X110.104 Y109.068 E.00146
; LINE_WIDTH: 0.183696
G1 X110.265 Y109.051 E.00186
; LINE_WIDTH: 0.217752
G1 X110.427 Y109.034 E.00231
; LINE_WIDTH: 0.246449
G1 X110.595 Y109.005 E.00283
; WIPE_START
G1 X110.427 Y109.034 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.373 Y116.075 Z1 F42000
G1 X113.897 Y117.328 Z1
G1 Z.6
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.49492
G1 F7964.602
M204 S6000
G1 X113.897 Y110.743 E.24253
M204 S10000
G1 X113.483 Y110.492 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X113.483 Y117.742 E.22277
G1 X114.312 Y117.742 E.02547
G1 X114.312 Y109.64 E.24897
G1 X113.63 Y110.365 E.03059
G1 X113.528 Y110.453 E.00413
M204 S10000
G1 X113.106 Y110.311 F42000
G1 F9547.299
M204 S6000
G1 X113.106 Y118.119 E.23994
G1 X114.689 Y118.119 E.04865
G1 X114.689 Y108.36 E.29988
G1 X114.441 Y108.811 E.01583
G1 X113.956 Y109.485 E.02551
G1 X113.364 Y110.097 E.02615
G1 X113.152 Y110.272 E.00846
M204 S10000
G1 X114.968 Y106.59 F42000
; LINE_WIDTH: 0.60044
G1 F6457.168
M204 S6000
G1 X114.983 Y106.225 E.0166
; LINE_WIDTH: 0.573248
G1 F6788.251
G2 X114.979 Y105.085 I-8.482 J-.536 E.04932
; LINE_WIDTH: 0.614925
G1 F6293.652
G1 X114.961 Y104.888 E.00921
; LINE_WIDTH: 0.655615
G1 F5875.681
G1 X114.943 Y104.691 E.00986
M204 S10000
G1 X114.968 Y106.59 F42000
; LINE_WIDTH: 0.591167
G1 F6566.392
M204 S6000
G1 X114.908 Y106.748 E.00755
; LINE_WIDTH: 0.542259
G1 F7209.535
G1 X114.848 Y106.907 E.00688
; LINE_WIDTH: 0.493352
G1 F7992.341
G1 X114.789 Y107.065 E.00621
; LINE_WIDTH: 0.420151
G1 F9543.227
G2 X114.473 Y107.941 I22.061 J8.437 E.02863
G1 X114.11 Y108.63 E.02393
G1 X113.655 Y109.259 E.02387
G1 X113.099 Y109.829 E.02448
G1 X112.729 Y110.121 E.0145
G1 X112.729 Y118.496 E.25745
G1 X115.066 Y118.496 E.07185
G1 X115.066 Y107.26 E.3454
; LINE_WIDTH: 0.440509
G1 F9054.582
G1 X115.045 Y107.109 E.00495
; LINE_WIDTH: 0.481547
G1 F8207.443
G1 X115.025 Y106.957 E.00546
; LINE_WIDTH: 0.522584
G1 F7505.258
G1 X115.004 Y106.806 E.00597
; LINE_WIDTH: 0.563622
G1 F6913.754
G1 X114.984 Y106.654 E.00648
; LINE_WIDTH: 0.59988
G1 F6463.66
G1 X114.982 Y106.649 E.00027
M204 S10000
G1 X114.283 Y104.127 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G3 X113.78 Y108.449 I-4.896 J1.621 E.13802
G1 X113.353 Y109.032 E.02221
G1 X112.833 Y109.561 E.02279
G1 X112.352 Y109.932 E.01868
G1 X112.352 Y118.873 E.27474
G1 X115.443 Y118.873 E.09499
G1 X115.443 Y104.127 E.45312
G1 X114.343 Y104.127 E.03381
M204 S10000
G1 X113.731 Y103.75 F42000
G1 F9547.299
M204 S6000
G1 X113.979 Y104.393 E.02118
G1 X114.128 Y105.065 E.02115
G1 X114.179 Y105.719 E.02018
G1 X114.136 Y106.387 E.02055
G1 X113.993 Y107.059 E.02112
G1 X113.767 Y107.676 E.02018
G3 X112.045 Y109.691 I-4.314 J-1.945 E.08255
G1 X111.979 Y109.738 E.00249
G1 X111.974 Y119.251 E.2923
G1 X115.82 Y119.251 E.11816
G1 X115.82 Y103.749 E.47629
G1 X113.791 Y103.749 E.06233
M204 S10000
G1 X113.086 Y103.372 F42000
G1 F9547.299
M204 S6000
G1 X113.41 Y103.948 E.02029
G3 X111.597 Y109.511 I-3.954 J1.788 E.19729
G1 X111.597 Y119.628 E.31085
G1 X116.197 Y119.628 E.14133
G1 X116.197 Y103.614 E.49205
G1 X116.165 Y103.372 E.00748
G1 X113.146 Y103.372 E.09276
; CHANGE_LAYER
; Z_HEIGHT: 0.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X115.146 Y103.372 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 4/79
; update layer progress
M73 L4
M991 S0 P3 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z1 I-.298 J-1.18 P1  F42000
G1 X99.722 Y107.261 Z1
G1 Z.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.527 Y107.528 E.01097
G3 X97.213 Y103.057 I-2.045 J-1.776 E.3502
G3 X99.251 Y103.701 I.253 J2.747 E.07278
G3 X99.761 Y107.216 I-1.768 J2.052 E.12851
M204 S10000
G1 X99.426 Y106.971 F42000
G1 F8843.478
M204 S6000
G1 X99.408 Y106.992 E.00092
G3 X97.242 Y103.463 I-1.933 J-1.243 E.30796
G3 X98.516 Y103.7 I.228 J2.313 E.04354
G3 X99.565 Y106.705 I-1.04 J2.049 E.11662
G1 X99.454 Y106.918 E.00799
M204 S250
G1 X99.087 Y106.786 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.27 Y103.854 I-1.602 J-1.036 E.23603
G3 X98.013 Y103.917 I.2 J2.06 E.02304
G3 X99.118 Y106.735 I-.529 J1.833 E.10742
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.12641
G1 X98.726 Y107.194 E-.10357
G1 X98.508 Y107.357 E-.1036
G1 X98.269 Y107.488 E-.10358
G1 X98.013 Y107.583 E-.10359
G1 X97.747 Y107.641 E-.10357
G1 X97.475 Y107.661 E-.10362
G1 X97.443 Y107.658 E-.01207
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X95.165 Y103.084 E.01901
G1 X94.798 Y103.45 E.01718
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.165 Y103.084 E-.22602
G1 X94.798 Y103.45 E-.19686
G1 X94.798 Y102.573 E-.33321
G1 X94.809 Y102.573 E-.00391
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01719
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29243
G1 X94.798 Y108.05 E-.33323
G1 X94.905 Y108.156 E-.05713
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z1.2 F42000
G1 X106.691 Y108.52 Z1.2
G1 Z.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21179
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.311 J-2.128 E.14916
G1 X100.306 Y102.98 E.02659
G1 X106.646 Y102.98 E.21031
G1 X106.17 Y103.613 E.02626
G1 X105.905 Y104.095 E.01824
G2 X106.649 Y108.477 I3.577 J1.647 E.15666
; WIPE_START
G1 X104.649 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.622 Y108.76 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.567 Y108.927 E.00583
G1 X99.382 Y108.927 E.27149
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18577
G2 X99.327 Y102.74 I-3.357 J2.283 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.571 Y102.573 E.27164
G1 X107.626 Y102.742 E.00588
G2 X107.159 Y108.411 I1.875 J3.008 E.21902
G1 X107.574 Y108.724 E.01723
; WIPE_START
G1 X107.567 Y108.927 E-.07715
G1 X105.77 Y108.927 E-.68285
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.677 Y108.623 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.348 Y108.745 E.01166
G3 X109.337 Y102.64 I-.866 J-2.993 E.34898
G3 X111.837 Y103.712 I.152 J3.096 E.09342
G3 X110.763 Y108.592 I-2.355 J2.04 E.19232
G1 X110.734 Y108.603 E.00104
M204 S10000
G1 X110.536 Y108.241 F42000
G1 F8843.478
M204 S6000
G1 X110.231 Y108.348 E.01071
G3 X109.363 Y103.046 I-.756 J-2.598 E.30372
G3 X110.841 Y103.414 I.102 J2.742 E.05119
G3 X110.592 Y108.214 I-1.366 J2.336 E.1963
G1 X110.59 Y108.215 E.00007
M204 S10000
G1 X110.395 Y107.86 F42000
G1 F8843.478
M204 S6000
G1 X110.119 Y107.962 E.00978
G3 X109.389 Y103.452 I-.635 J-2.211 E.25795
G3 X110.437 Y103.657 I.105 J2.245 E.03576
G3 X110.451 Y107.838 I-.953 J2.094 E.17405
M204 S250
G1 X110.259 Y107.492 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.009 Y107.585 E.00821
G3 X109.414 Y103.844 I-.527 J-1.834 E.19855
G3 X110.273 Y104.014 I.075 J1.868 E.02717
G3 X110.314 Y107.468 I-.792 J1.736 E.13268
; WIPE_START
M204 S6000
G1 X110.009 Y107.585 E-.12421
G1 X109.807 Y107.628 E-.07852
G1 X109.47 Y107.661 E-.12858
G1 X109.198 Y107.64 E-.10349
G1 X108.931 Y107.581 E-.10409
G1 X108.677 Y107.486 E-.10315
G1 X108.438 Y107.354 E-.1036
G1 X108.407 Y107.332 E-.01435
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.306 Y102.98 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.13927
G1 X116.627 Y103.832 E.02856
G1 X116.627 Y120.02 E.53696
G1 X111.205 Y120.02 E.17985
G1 X111.205 Y109.278 E.35633
G2 X112.19 Y108.587 I-1.846 J-3.682 E.04004
G2 X112.672 Y103.469 I-2.721 J-2.838 E.18589
G1 X112.342 Y103.028 E.01824
; WIPE_START
G1 X114.342 Y103.005 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.383 Y102.573 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18305
G1 X116.902 Y102.88 E.01018
G1 X117.034 Y103.803 E.03094
G1 X117.034 Y120.427 E.55143
G1 X110.798 Y120.427 E.20686
G1 X110.798 Y109.012 E.37863
G1 X110.932 Y108.963 E.00471
G2 X111.793 Y103.09 I-1.473 J-3.216 E.23363
G1 X111.328 Y102.74 E.01931
G1 X111.364 Y102.63 E.00384
; WIPE_START
G1 X113.364 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.734 Y102.431 Z1.2 F42000
G1 X94.391 Y102.166 Z1.2
G1 Z.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
M73 P38 R15
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.441 Y103.774 E.03094
G1 X117.441 Y120.834 E.56589
G1 X110.391 Y120.834 E.23386
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.961 E.0787
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00428
G2 X94.85 Y104.063 I2.834 J-1.296 E.54601
G1 X94.711 Y104.319 E.00967
G2 X94.592 Y104.575 I.829 J.54 E.00938
G1 X94.391 Y104.539 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z1.2 F42000
G1 X61.755 Y60.52 Z1.2
G1 Z.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X117.848 Y103.745 E.03094
G1 X117.848 Y121.241 E.58036
G1 X109.984 Y121.241 E.26087
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.255 Y103.716 E.03094
G1 X118.255 Y121.648 E.59483
G1 X109.577 Y121.648 E.28788
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.647 Y103.688 E.02866
G1 X118.647 Y121.815 E.55699
G1 X118.573 Y122.04 E.00728
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z1.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z1.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z1.2 F4000
            G39.3 S1
            G0 Z1.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z1.2 F42000
G1 X61.959 Y60.25 Z1.2
G1 Z.8
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.065 Y103.04 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
; LINE_WIDTH: 0.107367
M73 P39 R15
G1 F15000
M204 S6000
G1 X111.949 Y102.906 E.00093
; LINE_WIDTH: 0.133529
G1 X111.82 Y102.777 E.00135
M204 S10000
G1 X111.155 Y102.613 F42000
; LINE_WIDTH: 0.428264
G1 F9342.319
M204 S6000
G2 X110.927 Y102.556 I-.921 J3.179 E.00738
; LINE_WIDTH: 0.393148
G1 F10279.035
G1 X110.809 Y102.534 E.00342
; LINE_WIDTH: 0.35026
G1 F11713.426
G1 X110.692 Y102.513 E.003
; LINE_WIDTH: 0.307372
G1 F13613.069
G1 X110.574 Y102.491 E.00258
; LINE_WIDTH: 0.261984
G1 F15000
G1 X110.442 Y102.468 E.00239
; LINE_WIDTH: 0.221707
G1 X110.283 Y102.451 E.00232
; LINE_WIDTH: 0.187249
G1 X110.125 Y102.433 E.00187
; LINE_WIDTH: 0.152086
G1 X109.961 Y102.416 E.00147
; LINE_WIDTH: 0.116809
G1 X109.491 Y102.398 E.00283
G2 X108.999 Y102.415 I-.013 J6.883 E.00296
; LINE_WIDTH: 0.150045
G1 X108.842 Y102.432 E.00138
; LINE_WIDTH: 0.183427
G1 X108.685 Y102.448 E.00181
; LINE_WIDTH: 0.218313
G1 X108.514 Y102.467 E.00246
; LINE_WIDTH: 0.258625
G1 X108.395 Y102.488 E.00212
; LINE_WIDTH: 0.301047
G1 F13946.664
G1 X108.277 Y102.509 E.00253
; LINE_WIDTH: 0.343468
G1 F11978.13
G1 X108.158 Y102.531 E.00295
; LINE_WIDTH: 0.38589
G1 F10496.568
G1 X108.04 Y102.552 E.00336
; LINE_WIDTH: 0.423857
G1 F9450.379
G2 X107.798 Y102.612 I.734 J3.457 E.00773
M204 S10000
G1 X107.131 Y102.777 F42000
; LINE_WIDTH: 0.119818
G1 F15000
M204 S6000
G1 X106.893 Y103.033 E.00219
; WIPE_START
G1 X107.131 Y102.777 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X101.089 Y103.372 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X101.406 Y103.94 E.01997
G3 X101.632 Y106.957 I-4.113 J1.824 E.0948
G3 X101.089 Y108.128 I-4.071 J-1.174 E.03981
G1 X105.862 Y108.128 E.14665
G1 X105.538 Y107.549 E.02036
G3 X105.321 Y104.535 I4.116 J-1.812 E.09471
G3 X105.848 Y103.389 I4.218 J1.244 E.03889
G1 X105.231 Y103.372 E.01895
G1 X101.149 Y103.372 E.12543
M204 S10000
G1 X101.732 Y103.75 F42000
G1 F9547.299
M204 S6000
G1 X101.977 Y104.386 E.02096
G1 X102.126 Y105.041 E.02062
G3 X102 Y107.037 I-5.278 J.67 E.06182
G2 X101.743 Y107.751 I14.487 J5.618 E.02331
G1 X105.219 Y107.751 E.1068
G1 X104.97 Y107.104 E.02128
G1 X104.821 Y106.434 E.02111
G3 X104.953 Y104.454 I5.255 J-.645 E.06133
G1 X105.218 Y103.75 E.02312
G1 X101.792 Y103.75 E.10527
M204 S10000
G1 X102.283 Y104.127 F42000
G1 F9547.299
M204 S6000
G1 X102.494 Y104.96 E.02643
G1 X102.554 Y105.666 E.02176
G1 X102.518 Y106.345 E.02091
G1 X102.368 Y107.117 E.02414
G1 X102.283 Y107.373 E.00831
G1 X104.667 Y107.373 E.07326
G1 X104.453 Y106.512 E.02728
G1 X104.396 Y105.82 E.02133
G1 X104.433 Y105.158 E.02038
G1 X104.585 Y104.372 E.02458
G1 X104.667 Y104.127 E.00797
G1 X102.343 Y104.127 E.07141
M204 S10000
G1 X102.781 Y104.504 F42000
G1 F9547.299
M204 S6000
G3 X102.781 Y106.996 I-5.098 J1.246 E.07733
G1 X104.17 Y106.996 E.04269
G3 X104.17 Y104.504 I5.116 J-1.247 E.07733
G1 X102.841 Y104.504 E.04084
M204 S10000
G1 X103.253 Y104.889 F42000
; LINE_WIDTH: 0.423986
G1 F9447.18
M204 S6000
G3 X103.252 Y106.611 I-9.642 J.859 E.05353
G1 X103.698 Y106.611 E.01385
G3 X103.697 Y104.889 I9.56 J-.865 E.05353
G1 X103.313 Y104.889 E.01195
; WIPE_START
G1 X103.697 Y104.889 E-.14625
G1 X103.672 Y105.101 E-.0811
G1 X103.653 Y105.871 E-.29253
G1 X103.692 Y106.502 E-.24012
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z1.2 F42000
G1 Z.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108318
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134115
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.42643
G1 F9386.976
M204 S6000
G2 X98.92 Y102.554 I-.943 J3.259 E.00755
; LINE_WIDTH: 0.389879
G1 F10375.871
G1 X98.802 Y102.533 E.00341
; LINE_WIDTH: 0.347097
G1 F11835.241
G1 X98.683 Y102.511 E.00299
; LINE_WIDTH: 0.304314
G1 F13772.323
G1 X98.564 Y102.49 E.00257
; LINE_WIDTH: 0.259083
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219138
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185147
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150471
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.11635
G1 X97.473 Y102.398 E.00286
G2 X96.992 Y102.415 I-.004 J6.528 E.00288
; LINE_WIDTH: 0.151139
G1 X96.834 Y102.432 E.0014
; LINE_WIDTH: 0.185132
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.22067
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.261525
G1 X96.386 Y102.49 E.00215
; LINE_WIDTH: 0.30433
G1 F13771.505
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347134
G1 F11833.791
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.389938
G1 F10374.106
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426469
G1 F9386.042
G2 X95.796 Y102.613 I.722 J3.379 E.00755
M204 S10000
G1 X94.732 Y103.839 F42000
; LINE_WIDTH: 0.106662
G1 F15000
M204 S6000
G1 X94.649 Y103.937 E.00067
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497425
G1 F7920.707
M204 S6000
G1 X94.419 Y105.024 E.00999
; LINE_WIDTH: 0.463227
G1 F8565.176
G2 X94.389 Y105.321 I4.134 J.58 E.01023
; LINE_WIDTH: 0.429914
G1 F9302.48
G2 X94.391 Y106.208 I8.943 J.423 E.028
; LINE_WIDTH: 0.464995
G1 F8529.305
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.497398
G1 F7921.174
G1 X94.448 Y106.744 E.00998
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.106648
G1 F15000
M204 S6000
G2 X94.649 Y107.564 I.126 J.005 E.00052
G1 X94.732 Y107.66 E.00066
M204 S10000
G1 X95.796 Y108.887 F42000
; LINE_WIDTH: 0.426418
G1 F9387.292
M204 S6000
G2 X96.03 Y108.946 I.936 J-3.231 E.00755
; LINE_WIDTH: 0.389874
G1 F10376.011
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.34711
G1 F11834.705
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304346
G1 F13770.623
G1 X96.386 Y109.01 E.00257
; LINE_WIDTH: 0.261582
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.220737
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185188
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.151183
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.116375
G2 X97.473 Y109.102 I.487 J-6.82 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.150503
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185193
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219198
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259148
G1 X98.565 Y109.01 E.00237
; LINE_WIDTH: 0.304373
G1 F13769.202
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.347152
G1 F11833.081
G1 X98.802 Y108.967 E.00299
; LINE_WIDTH: 0.389931
G1 F10374.323
G1 X98.92 Y108.946 E.00341
; LINE_WIDTH: 0.426458
G1 F9386.299
G2 X99.154 Y108.887 I-.72 J-3.368 E.00755
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.134133
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.108308
G1 X100.065 Y108.46 E.001
; WIPE_START
G1 X99.942 Y108.601 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.57 Y108.879 Z1.2 F42000
G1 X107.795 Y108.887 Z1.2
G1 Z.8
G1 E.8 F1800
; LINE_WIDTH: 0.428799
G1 F9329.363
M204 S6000
G2 X108.02 Y108.944 I.934 J-3.234 E.00732
; LINE_WIDTH: 0.394307
G1 F10245.136
G1 X108.137 Y108.965 E.00339
; LINE_WIDTH: 0.351962
G1 F11648.917
G1 X108.253 Y108.986 E.00298
; LINE_WIDTH: 0.309617
G1 F13498.466
G1 X108.37 Y109.008 E.00257
; LINE_WIDTH: 0.267273
G1 F15000
G1 X108.486 Y109.029 E.00216
; LINE_WIDTH: 0.224221
G1 X108.67 Y109.05 E.00274
; LINE_WIDTH: 0.186158
G1 X108.828 Y109.067 E.00186
; LINE_WIDTH: 0.152256
G1 X108.985 Y109.084 E.00141
; LINE_WIDTH: 0.116233
G2 X109.464 Y109.102 I.501 J-6.973 E.00286
G1 X109.933 Y109.086 E.00281
; LINE_WIDTH: 0.148619
G1 X110.101 Y109.069 E.00145
; LINE_WIDTH: 0.183289
G1 X110.263 Y109.052 E.00186
; LINE_WIDTH: 0.21731
G1 X110.425 Y109.035 E.00231
; LINE_WIDTH: 0.24625
G1 X110.595 Y109.005 E.00286
; WIPE_START
G1 X110.425 Y109.035 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.392 Y116.067 Z1.2 F42000
G1 X113.916 Y117.309 Z1.2
G1 Z.8
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.53276
G1 F7349.338
M204 S6000
G1 X113.916 Y110.751 E.26177
M204 S10000
G1 X113.483 Y110.492 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X113.483 Y117.742 E.22278
G1 X114.35 Y117.742 E.02664
G1 X114.35 Y109.589 E.25052
G3 X113.528 Y110.453 I-5.953 J-4.837 E.03666
M204 S10000
G1 X114.725 Y108.298 F42000
G1 F9547.299
M204 S6000
G1 X114.439 Y108.815 E.01816
G1 X113.954 Y109.488 E.02549
G1 X113.361 Y110.099 E.02615
G1 X113.106 Y110.311 E.01019
G1 X113.106 Y118.119 E.23993
G1 X114.727 Y118.119 E.04981
G2 X114.725 Y108.358 I-1533.11 J-4.615 E.29992
M204 S10000
G1 X114.753 Y104.482 F42000
; LINE_WIDTH: 0.35691
G1 F11465.333
M204 S6000
G1 X114.851 Y105.097 E.01595
; LINE_WIDTH: 0.328164
G1 F12620.769
G3 X114.848 Y106.442 I-7.109 J.655 E.03131
; LINE_WIDTH: 0.35975
G1 F11362.561
G1 X114.788 Y106.834 E.01023
; LINE_WIDTH: 0.419684
G1 F9555.064
G1 X114.728 Y107.226 E.01216
G1 X114.472 Y107.945 E.02344
G1 X114.108 Y108.634 E.02391
G1 X113.652 Y109.261 E.02382
G1 X113.096 Y109.832 E.02446
G1 X112.729 Y110.121 E.01437
G1 X112.729 Y118.496 E.25713
G1 X115.104 Y118.496 E.07292
G1 X115.104 Y107.267 E.34476
; LINE_WIDTH: 0.40506
G1 F9940.906
G1 X115.119 Y106.964 E.00895
; LINE_WIDTH: 0.3752
G1 F10834.237
G1 X115.134 Y106.661 E.00821
; LINE_WIDTH: 0.333433
G1 F12391.871
G2 X115.145 Y105.087 I-20.072 J-.933 E.03727
; LINE_WIDTH: 0.363542
G1 F11228.195
G1 X115.126 Y104.482 E.01583
G1 X114.813 Y104.482 E.00817
M204 S10000
G1 X114.283 Y104.127 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G3 X113.351 Y109.035 I-4.873 J1.618 E.1603
G1 X112.831 Y109.564 E.0228
G1 X112.352 Y109.932 E.01857
G1 X112.352 Y118.873 E.27474
G1 X115.481 Y118.873 E.09615
G1 X115.481 Y104.127 E.45312
G1 X114.343 Y104.127 E.03498
M204 S10000
G1 X113.731 Y103.75 F42000
G1 F9547.299
M204 S6000
G1 X113.98 Y104.395 E.02126
G1 X114.129 Y105.067 E.02115
G1 X114.179 Y105.723 E.0202
G1 X114.136 Y106.389 E.02053
G1 X113.992 Y107.062 E.02112
G1 X113.766 Y107.679 E.02021
G1 X113.447 Y108.27 E.02063
G1 X113.05 Y108.808 E.02053
G1 X112.566 Y109.296 E.02112
G3 X111.974 Y109.735 I-3.04 J-3.469 E.02266
G1 X111.974 Y119.251 E.29236
G1 X115.858 Y119.251 E.11933
G1 X115.858 Y103.898 E.47173
G1 X115.838 Y103.749 E.0046
G1 X113.791 Y103.749 E.0629
M204 S10000
G1 X113.086 Y103.372 F42000
G1 F9547.299
M204 S6000
G1 X113.412 Y103.951 E.0204
G3 X111.597 Y109.511 I-3.956 J1.785 E.19718
G1 X111.597 Y119.628 E.31084
G1 X116.235 Y119.628 E.1425
G1 X116.235 Y103.898 E.48332
G1 X116.165 Y103.372 E.01629
G1 X113.146 Y103.372 E.09276
; CHANGE_LAYER
; Z_HEIGHT: 1
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X115.146 Y103.372 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 5/79
; update layer progress
M73 L5
M991 S0 P4 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z1.2 I-.292 J-1.181 P1  F42000
G1 X99.783 Y107.166 Z1.2
G1 Z1
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.76 Y107.218 E.0019
G3 X97.228 Y103.056 I-2.277 J-1.466 E.36351
G3 X99.251 Y103.701 I.262 J2.674 E.0724
G3 X99.946 Y106.878 I-1.768 J2.052 E.11575
G1 X99.813 Y107.114 E.00897
M204 S10000
G1 X99.396 Y107.018 F42000
G1 F8843.478
M204 S6000
G1 X99.219 Y107.261 E.01
G3 X97.257 Y103.462 I-1.736 J-1.51 E.29754
G3 X98.72 Y103.812 I.212 J2.346 E.0508
G3 X99.434 Y106.971 I-1.238 J1.94 E.11918
M204 S250
G1 X99.085 Y106.785 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.285 Y103.853 I-1.602 J-1.035 E.23648
G3 X98.269 Y104.012 I.204 J1.859 E.03099
G3 X99.117 Y106.734 I-.786 J1.738 E.09894
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.12636
G1 X98.726 Y107.194 E-.1036
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10356
G1 X97.747 Y107.641 E-.10358
G1 X97.475 Y107.661 E-.1036
G1 X97.443 Y107.658 E-.01213
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z1.4 F42000
G1 Z1
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X94.798 Y103.45 I2.055 J3.224 E.03623
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.165 Y103.084 E-.22603
G1 X94.798 Y103.45 E-.19686
G1 X94.798 Y102.573 E-.33321
G1 X94.809 Y102.573 E-.0039
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z1.4 F42000
G1 Z1
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01719
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29243
G1 X94.798 Y108.05 E-.33324
G1 X94.905 Y108.156 E-.05712
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z1.4 F42000
G1 X106.691 Y108.52 Z1.4
G1 Z1
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21179
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.311 J-2.128 E.14916
G1 X100.306 Y102.98 E.02658
G1 X106.646 Y102.98 E.21033
G1 X106.171 Y103.61 E.02617
G1 X105.906 Y104.093 E.01828
G2 X106.649 Y108.477 I3.578 J1.649 E.15672
; WIPE_START
G1 X104.649 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.622 Y108.76 Z1.4 F42000
G1 Z1
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.566 Y108.927 E.00583
G1 X99.382 Y108.927 E.27148
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18578
G2 X99.327 Y102.74 I-3.356 J2.282 E.05236
G1 X99.382 Y102.573 E.00584
G1 X107.571 Y102.573 E.27164
G1 X107.626 Y102.742 E.00588
G2 X107.158 Y108.41 I1.875 J3.008 E.21895
G1 X107.574 Y108.724 E.0173
; WIPE_START
G1 X107.566 Y108.927 E-.07713
G1 X105.769 Y108.927 E-.68288
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.67 Y108.626 Z1.4 F42000
G1 Z1
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.346 Y108.746 E.01149
G3 X109.323 Y102.641 I-.864 J-2.994 E.34847
M73 P39 R14
G3 X111.838 Y103.714 I.166 J3.094 E.09394
G3 X110.761 Y108.594 I-2.356 J2.039 E.19235
G1 X110.727 Y108.606 E.00121
M204 S10000
G1 X110.53 Y108.244 F42000
G1 F8843.478
M204 S6000
G1 X110.231 Y108.354 E.01055
G3 X109.349 Y103.047 I-.749 J-2.602 E.30297
G3 X111.258 Y103.707 I.113 J2.763 E.06859
G3 X110.593 Y108.222 I-1.776 J2.045 E.18001
G1 X110.586 Y108.224 E.00024
M204 S10000
G1 X110.389 Y107.862 F42000
G1 F8843.478
M204 S6000
G1 X110.116 Y107.958 E.00959
G3 X109.375 Y103.453 I-.641 J-2.208 E.25779
G3 X110.633 Y103.764 I.092 J2.329 E.04354
G3 X110.442 Y107.835 I-1.157 J1.986 E.16621
M204 S250
G1 X110.253 Y107.494 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.007 Y107.586 E.00806
G3 X109.4 Y103.844 I-.525 J-1.835 E.19804
G3 X110.274 Y104.015 I.09 J1.864 E.02764
G3 X110.308 Y107.471 I-.792 J1.736 E.13287
; WIPE_START
M204 S6000
G1 X110.007 Y107.586 E-.12232
G1 X109.82 Y107.626 E-.07284
G1 X109.468 Y107.66 E-.13429
G1 X109.197 Y107.64 E-.10345
G1 X108.929 Y107.581 E-.1041
G1 X108.675 Y107.485 E-.10318
G1 X108.436 Y107.354 E-.10358
G1 X108.402 Y107.328 E-.01624
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.306 Y102.98 Z1.4 F42000
G1 Z1
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.13927
G1 X116.665 Y104.096 E.0374
G1 X116.665 Y120.02 E.52821
G1 X111.205 Y120.02 E.1811
G1 X111.205 Y109.278 E.35633
G2 X112.199 Y108.579 I-1.837 J-3.668 E.04045
G1 X112.443 Y108.335 E.01143
G2 X112.663 Y103.456 I-2.982 J-2.579 E.17471
G1 X112.342 Y103.028 E.01773
; WIPE_START
G1 X114.342 Y103.005 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.384 Y102.573 Z1.4 F42000
G1 Z1
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18304
G1 X116.902 Y102.88 E.01018
G1 X117.072 Y104.067 E.03978
G1 X117.072 Y120.427 E.54268
G1 X110.798 Y120.427 E.20811
G1 X110.798 Y109.013 E.37863
G1 X110.929 Y108.964 E.00463
G2 X111.795 Y103.092 I-1.471 J-3.217 E.23362
G1 X111.328 Y102.74 E.0194
G1 X111.365 Y102.63 E.00384
; WIPE_START
G1 X113.365 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.734 Y102.431 Z1.4 F42000
G1 X94.391 Y102.166 Z1.4
G1 Z1
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.479 Y104.038 E.03978
G1 X117.479 Y120.834 E.55714
G1 X110.391 Y120.834 E.23512
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.961 E.0787
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00428
G2 X94.637 Y104.454 I2.834 J-1.296 E.56074
G1 X94.592 Y104.575 E.00428
G1 X94.391 Y104.539 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z1.4 F42000
G1 X61.755 Y60.52 Z1.4
G1 Z1
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X117.886 Y104.009 E.03978
G1 X117.886 Y121.241 E.57161
G1 X109.984 Y121.241 E.26212
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
M73 P40 R14
G1 X118.293 Y103.98 E.03978
G1 X118.293 Y121.648 E.58608
G1 X109.577 Y121.648 E.28913
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.685 Y103.952 E.03685
G1 X118.685 Y121.701 E.54536
G1 X118.573 Y122.04 E.01099
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z1.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z1.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z1.4 F4000
            G39.3 S1
            G0 Z1.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z1
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z1.4 F42000
G1 X61.959 Y60.25 Z1.4
G1 Z1
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z1.4 F42000
G1 Z1
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.065 Y103.04 Z1.4 F42000
G1 Z1
G1 E.8 F1800
; LINE_WIDTH: 0.107094
G1 F15000
M204 S6000
G1 X111.952 Y102.908 E.00091
; LINE_WIDTH: 0.133352
G1 X111.82 Y102.777 E.00137
M204 S10000
G1 X111.156 Y102.613 F42000
; LINE_WIDTH: 0.428783
G1 F9329.748
M204 S6000
G2 X110.929 Y102.556 I-.929 J3.218 E.00734
; LINE_WIDTH: 0.394044
G1 F10252.798
G1 X110.812 Y102.535 E.00343
; LINE_WIDTH: 0.351117
G1 F11680.844
G1 X110.694 Y102.513 E.00301
; LINE_WIDTH: 0.30819
G1 F13571.072
G1 X110.576 Y102.492 E.00259
; LINE_WIDTH: 0.262749
G1 F15000
G1 X110.444 Y102.468 E.0024
; LINE_WIDTH: 0.222388
G1 X110.286 Y102.451 E.00232
; LINE_WIDTH: 0.187825
G1 X110.128 Y102.434 E.00188
; LINE_WIDTH: 0.152551
G1 X109.963 Y102.416 E.00148
; LINE_WIDTH: 0.116834
G1 X109.493 Y102.398 E.00284
G2 X109.001 Y102.415 I-.018 J6.775 E.00296
; LINE_WIDTH: 0.158001
G1 X108.766 Y102.44 E.00222
; LINE_WIDTH: 0.207814
G1 X108.53 Y102.465 E.00318
; LINE_WIDTH: 0.234679
G1 X108.517 Y102.467 E.00022
; LINE_WIDTH: 0.257772
G1 X108.398 Y102.488 E.00211
; LINE_WIDTH: 0.300106
G1 F13997.675
G1 X108.279 Y102.509 E.00252
; LINE_WIDTH: 0.34244
G1 F12019.257
M73 P41 R14
G1 X108.161 Y102.53 E.00294
; LINE_WIDTH: 0.384773
G1 F10530.838
G1 X108.042 Y102.551 E.00335
; LINE_WIDTH: 0.423263
G1 F9465.147
G2 X107.798 Y102.612 I.734 J3.463 E.00781
M204 S10000
G1 X107.132 Y102.777 F42000
; LINE_WIDTH: 0.11959
G1 F15000
M204 S6000
G1 X106.895 Y103.031 E.00217
; WIPE_START
G1 X107.132 Y102.777 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X101.089 Y103.372 Z1.4 F42000
G1 Z1
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X101.406 Y103.94 E.01997
G3 X101.632 Y106.957 I-4.112 J1.824 E.0948
G3 X101.089 Y108.128 I-4.07 J-1.174 E.03981
G1 X105.862 Y108.128 E.14666
G1 X105.537 Y107.546 E.02048
G3 X105.185 Y105.215 I3.906 J-1.782 E.07336
G1 X105.322 Y104.533 E.02139
G3 X105.85 Y103.386 I4.207 J1.241 E.03892
G1 X101.149 Y103.372 E.14443
M204 S10000
G1 X101.732 Y103.749 F42000
G1 F9547.299
M204 S6000
G1 X101.977 Y104.386 E.02096
G1 X102.126 Y105.041 E.02063
G3 X102 Y107.037 I-5.295 J.669 E.06182
G2 X101.743 Y107.751 I14.545 J5.639 E.02331
G1 X105.219 Y107.751 E.1068
G1 X104.969 Y107.102 E.02135
G1 X104.821 Y106.431 E.02111
G3 X104.954 Y104.451 I5.269 J-.641 E.06133
G1 X105.218 Y103.75 E.02304
G1 X101.792 Y103.749 E.10526
M204 S10000
G1 X102.283 Y104.127 F42000
G1 F9547.299
M204 S6000
G1 X102.494 Y104.96 E.02643
G1 X102.554 Y105.661 E.02161
G1 X102.518 Y106.346 E.02105
G1 X102.368 Y107.117 E.02414
G1 X102.283 Y107.373 E.00831
G1 X104.668 Y107.373 E.07327
G1 X104.452 Y106.509 E.02737
G1 X104.396 Y105.821 E.02123
G1 X104.433 Y105.159 E.02037
G1 X104.586 Y104.37 E.0247
G1 X104.667 Y104.127 E.00788
G1 X102.343 Y104.127 E.07141
M204 S10000
G1 X102.781 Y104.504 F42000
G1 F9547.299
M204 S6000
G3 X102.781 Y106.996 I-5.098 J1.246 E.07733
G1 X104.17 Y106.996 E.04269
G3 X104.17 Y104.504 I5.126 J-1.247 E.07732
G1 X102.841 Y104.504 E.04084
M204 S10000
G1 X103.253 Y104.889 F42000
; LINE_WIDTH: 0.424052
G1 F9445.566
M204 S6000
G3 X103.252 Y106.611 I-9.692 J.858 E.05353
G1 X103.698 Y106.611 E.01385
G3 X103.697 Y104.889 I9.61 J-.866 E.05354
G1 X103.313 Y104.889 E.01195
; WIPE_START
G1 X103.697 Y104.889 E-.14621
G1 X103.672 Y105.102 E-.08117
G1 X103.654 Y105.871 E-.29247
G1 X103.692 Y106.502 E-.24016
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z1.4 F42000
G1 Z1
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108272
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134066
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.426423
G1 F9387.168
M204 S6000
G2 X98.92 Y102.554 I-.941 J3.25 E.00755
; LINE_WIDTH: 0.389878
G1 F10375.903
G1 X98.802 Y102.533 E.00341
; LINE_WIDTH: 0.347107
G1 F11834.827
G1 X98.683 Y102.511 E.00299
; LINE_WIDTH: 0.304337
G1 F13771.144
G1 X98.565 Y102.49 E.00257
; LINE_WIDTH: 0.259119
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219178
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185179
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150494
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.116351
G1 X97.473 Y102.398 E.00286
G2 X96.992 Y102.415 I-.003 J6.555 E.00288
; LINE_WIDTH: 0.151156
G1 X96.834 Y102.432 E.0014
; LINE_WIDTH: 0.185133
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.220657
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.261512
G1 X96.386 Y102.49 E.00215
; LINE_WIDTH: 0.304325
G1 F13771.729
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347139
G1 F11833.577
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.389953
G1 F10373.653
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426481
G1 F9385.738
G2 X95.796 Y102.613 I.706 J3.31 E.00755
M204 S10000
G1 X94.732 Y103.839 F42000
; LINE_WIDTH: 0.106658
G1 F15000
M204 S6000
G1 X94.649 Y103.936 E.00067
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497405
G1 F7921.068
M204 S6000
G1 X94.419 Y105.024 E.00998
; LINE_WIDTH: 0.463221
G1 F8565.3
G2 X94.389 Y105.321 I4.135 J.58 E.01022
; LINE_WIDTH: 0.429914
G1 F9302.476
G2 X94.391 Y106.208 I8.943 J.423 E.028
; LINE_WIDTH: 0.465003
G1 F8529.14
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.497414
G1 F7920.894
G1 X94.448 Y106.744 E.00998
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.106637
G1 F15000
M204 S6000
G2 X94.649 Y107.564 I.127 J.005 E.00052
G1 X94.732 Y107.66 E.00066
M204 S10000
G1 X95.796 Y108.887 F42000
; LINE_WIDTH: 0.426422
G1 F9387.194
M204 S6000
G2 X96.03 Y108.946 I.947 J-3.273 E.00755
; LINE_WIDTH: 0.389891
G1 F10375.521
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.347122
G1 F11834.249
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304353
G1 F13770.254
G1 X96.386 Y109.01 E.00257
; LINE_WIDTH: 0.261585
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.220743
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185201
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.1512
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.11637
G2 X97.473 Y109.102 I.477 J-6.538 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.1505
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185183
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219181
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259132
G1 X98.564 Y109.01 E.00237
; LINE_WIDTH: 0.304339
G1 F13771.014
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.3471
G1 F11835.128
G1 X98.801 Y108.968 E.00298
; LINE_WIDTH: 0.38986
G1 F10376.443
G1 X98.92 Y108.946 E.0034
; LINE_WIDTH: 0.426427
G1 F9387.052
G2 X99.154 Y108.887 I-.708 J-3.314 E.00756
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.134063
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.10827
G1 X100.065 Y108.46 E.001
; WIPE_START
G1 X99.942 Y108.601 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.57 Y108.879 Z1.4 F42000
G1 X107.794 Y108.887 Z1.4
G1 Z1
G1 E.8 F1800
; LINE_WIDTH: 0.429446
G1 F9313.753
M204 S6000
G2 X108.018 Y108.943 I.913 J-3.149 E.00725
; LINE_WIDTH: 0.395374
G1 F10214.111
G1 X108.134 Y108.965 E.0034
; LINE_WIDTH: 0.352879
G1 F11614.466
G1 X108.251 Y108.986 E.00299
; LINE_WIDTH: 0.310383
G1 F13459.806
G1 X108.367 Y109.007 E.00258
; LINE_WIDTH: 0.267888
G1 F15000
G1 X108.484 Y109.028 E.00217
; LINE_WIDTH: 0.223098
G1 X108.683 Y109.052 E.00293
; LINE_WIDTH: 0.184178
G1 X108.833 Y109.068 E.00175
; LINE_WIDTH: 0.15185
G1 X108.983 Y109.084 E.00134
; LINE_WIDTH: 0.116251
G2 X109.461 Y109.102 I.495 J-6.722 E.00286
G1 X109.931 Y109.086 E.00281
; LINE_WIDTH: 0.148269
G1 X110.099 Y109.069 E.00145
; LINE_WIDTH: 0.182862
G1 X110.261 Y109.052 E.00185
; LINE_WIDTH: 0.216808
G1 X110.423 Y109.035 E.0023
; LINE_WIDTH: 0.246023
G1 X110.595 Y109.005 E.00289
; WIPE_START
G1 X110.423 Y109.035 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.411 Y116.058 Z1.4 F42000
G1 X113.935 Y117.29 Z1.4
G1 Z1
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.5706
G1 F6822.317
M204 S6000
G1 X113.935 Y110.759 E.28083
M204 S10000
G1 X113.483 Y110.492 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X113.483 Y117.742 E.22279
G1 X114.388 Y117.742 E.0278
G1 X114.388 Y109.539 E.25207
G3 X113.528 Y110.453 I-5.772 J-4.564 E.03859
M204 S10000
G1 X114.765 Y108.207 F42000
G1 F9547.299
M204 S6000
G1 X114.436 Y108.819 E.02134
G1 X113.951 Y109.491 E.02547
G1 X113.36 Y110.101 E.02608
G1 X113.106 Y110.311 E.01015
G1 X113.106 Y118.119 E.23992
G1 X114.765 Y118.119 E.05097
G1 X114.765 Y108.267 E.30271
M204 S10000
G1 X114.763 Y104.49 F42000
; LINE_WIDTH: 0.37477
G1 F10848.274
M204 S6000
G1 X114.861 Y105.1 E.01669
; LINE_WIDTH: 0.347131
G1 F11833.89
G3 X114.857 Y106.447 I-7.116 J.652 E.03344
; LINE_WIDTH: 0.374173
G1 F10867.842
G1 X114.792 Y106.837 E.01069
; LINE_WIDTH: 0.419269
G1 F9565.605
G1 X114.728 Y107.228 E.01214
G1 X114.47 Y107.949 E.02349
G1 X114.106 Y108.637 E.02388
G1 X113.65 Y109.264 E.02377
G1 X113.095 Y109.833 E.02436
G1 X112.729 Y110.121 E.0143
G1 X112.729 Y118.496 E.25684
G1 X115.142 Y118.496 E.074
G1 X115.142 Y107.273 E.34418
G1 X115.163 Y106.668 E.01856
; LINE_WIDTH: 0.351679
G1 F11659.606
G2 X115.174 Y105.089 I-21.213 J-.927 E.03974
; LINE_WIDTH: 0.381392
G1 F10636.05
G1 X115.155 Y104.49 E.01653
G1 X114.823 Y104.49 E.00914
M204 S10000
G1 X114.282 Y104.127 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G3 X112.83 Y109.565 I-4.854 J1.616 E.18313
G1 X112.352 Y109.932 E.01852
G1 X112.352 Y118.873 E.27475
G1 X115.519 Y118.873 E.09732
G1 X115.519 Y104.182 E.45142
G1 X115.511 Y104.127 E.00172
G1 X114.342 Y104.127 E.03592
M204 S10000
G1 X113.731 Y103.749 F42000
G1 F9547.299
M204 S6000
G1 X113.981 Y104.398 E.02135
G1 X114.129 Y105.07 E.02115
G3 X113.991 Y107.064 I-5.197 J.643 E.06179
G1 X113.764 Y107.683 E.02027
G1 X113.445 Y108.274 E.02063
G1 X113.048 Y108.81 E.02051
G1 X112.565 Y109.297 E.02108
G3 X111.974 Y109.735 I-3.03 J-3.459 E.02262
G1 X111.974 Y119.251 E.29236
G1 X115.896 Y119.251 E.12049
G1 X115.896 Y104.182 E.463
G1 X115.838 Y103.749 E.01341
G1 X113.791 Y103.749 E.0629
M204 S10000
G1 X113.086 Y103.372 F42000
G1 F9547.299
M204 S6000
G1 X113.413 Y103.954 E.0205
G3 X111.597 Y109.511 I-3.958 J1.782 E.19708
G1 X111.597 Y119.628 E.31084
G1 X116.273 Y119.628 E.14366
G1 X116.273 Y104.182 E.47459
G1 X116.165 Y103.372 E.02509
G1 X113.146 Y103.372 E.09276
; CHANGE_LAYER
; Z_HEIGHT: 1.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X115.146 Y103.372 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 6/79
; update layer progress
M73 L6
M991 S0 P5 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z1.4 I-.298 J-1.18 P1  F42000
G1 X99.722 Y107.262 Z1.4
G1 Z1.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.527 Y107.528 E.01096
G3 X97.243 Y103.055 I-2.045 J-1.775 E.35118
G3 X99.524 Y103.974 I.227 J2.727 E.08462
G3 X99.761 Y107.216 I-2.043 J1.778 E.11563
M204 S10000
G1 X99.396 Y107.018 F42000
G1 F8843.478
M204 S6000
G1 X99.219 Y107.262 E.01
G3 X97.272 Y103.461 I-1.736 J-1.51 E.29798
G3 X98.72 Y103.812 I.198 J2.344 E.0503
G3 X99.434 Y106.972 I-1.237 J1.94 E.1192
M204 S250
G1 X99.087 Y106.786 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.3 Y103.852 I-1.603 J-1.035 E.23704
G3 X98.269 Y104.012 I.191 J1.856 E.03053
G3 X99.119 Y106.735 I-.785 J1.739 E.099
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.12644
G1 X98.726 Y107.194 E-.10358
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10357
G1 X97.747 Y107.641 E-.10358
G1 X97.475 Y107.661 E-.10362
G1 X97.443 Y107.658 E-.01204
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X94.798 Y103.45 I2.055 J3.223 E.03623
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.165 Y103.084 E-.22602
G1 X94.798 Y103.45 E-.19688
G1 X94.798 Y102.573 E-.33322
G1 X94.808 Y102.573 E-.00388
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01719
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29242
G1 X94.798 Y108.05 E-.33322
G1 X94.905 Y108.156 E-.05714
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z1.6 F42000
G1 X106.691 Y108.52 Z1.6
G1 Z1.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.2118
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.375 J-2.128 E.1489
G1 X100.306 Y102.98 E.02659
G1 X106.647 Y102.98 E.21035
G1 X106.173 Y103.608 E.02608
G1 X105.906 Y104.091 E.01831
G2 X106.649 Y108.477 I3.579 J1.65 E.15679
; WIPE_START
G1 X104.649 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.622 Y108.76 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.566 Y108.927 E.00583
G1 X99.382 Y108.927 E.27147
G1 X99.327 Y108.76 E.00584
G2 X100.684 Y104.284 I-1.898 J-3.019 E.16919
G1 X100.443 Y103.843 E.01669
G2 X99.327 Y102.74 I-3.356 J2.282 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.571 Y102.573 E.27165
G1 X107.626 Y102.742 E.00588
G2 X107.156 Y108.409 I1.874 J3.008 E.21889
G1 X107.574 Y108.724 E.01736
; WIPE_START
G1 X107.566 Y108.927 E-.07711
G1 X105.769 Y108.927 E-.68289
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.663 Y108.629 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.344 Y108.747 E.0113
G3 X109.31 Y102.642 I-.862 J-2.994 E.34796
G3 X111.839 Y103.715 I.18 J3.093 E.09444
G3 X110.759 Y108.595 I-2.357 J2.037 E.19238
G1 X110.72 Y108.609 E.00138
M204 S10000
G1 X110.523 Y108.247 F42000
G1 F8843.478
M204 S6000
G1 X110.23 Y108.354 E.01036
G3 X109.336 Y103.048 I-.747 J-2.603 E.30243
G3 X111.26 Y103.708 I.127 J2.761 E.0691
G3 X110.591 Y108.222 I-1.777 J2.043 E.18002
G1 X110.579 Y108.226 E.00041
M204 S10000
G1 X110.382 Y107.865 F42000
G1 F8843.478
M204 S6000
G1 X110.114 Y107.958 E.00942
G3 X109.362 Y103.454 I-.639 J-2.208 E.2573
G3 X110.621 Y103.757 I.107 J2.322 E.04352
G3 X110.436 Y107.838 I-1.146 J1.993 E.16688
M204 S250
G1 X110.247 Y107.497 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.006 Y107.586 E.0079
G3 X109.387 Y103.845 I-.523 J-1.835 E.19755
G3 X110.276 Y104.016 I.104 J1.861 E.02809
G3 X110.302 Y107.474 I-.793 J1.736 E.13305
; WIPE_START
M204 S6000
G1 X110.006 Y107.586 E-.12035
G1 X109.833 Y107.623 E-.06713
G1 X109.467 Y107.66 E-.13998
G1 X109.195 Y107.64 E-.10342
G1 X108.928 Y107.58 E-.10408
G1 X108.674 Y107.484 E-.10326
G1 X108.435 Y107.353 E-.10358
G1 X108.397 Y107.324 E-.01821
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.306 Y102.98 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.13927
G1 X116.703 Y104.36 E.04624
G1 X116.703 Y120.02 E.51946
G1 X111.205 Y120.02 E.18236
G1 X111.205 Y109.277 E.35634
G2 X112.208 Y108.57 I-1.829 J-3.656 E.04086
G1 X112.441 Y108.337 E.01096
G2 X112.657 Y103.448 I-2.981 J-2.58 E.1751
G1 X112.342 Y103.028 E.01739
; WIPE_START
G1 X114.342 Y103.005 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.384 Y102.573 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18303
G1 X116.902 Y102.88 E.01018
G1 X117.11 Y104.331 E.04862
G1 X117.11 Y120.427 E.53393
G1 X110.798 Y120.427 E.20937
G1 X110.798 Y109.013 E.37863
G1 X110.926 Y108.965 E.00453
G2 X111.797 Y103.094 I-1.469 J-3.218 E.23361
G1 X111.328 Y102.74 E.01948
G1 X111.365 Y102.63 E.00384
; WIPE_START
G1 X113.365 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.734 Y102.431 Z1.6 F42000
G1 X94.391 Y102.166 Z1.6
G1 Z1.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.517 Y104.302 E.04862
G1 X117.517 Y120.834 E.54839
G1 X110.391 Y120.834 E.23637
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.961 E.07869
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00428
G2 X94.637 Y104.454 I2.834 J-1.296 E.56078
G1 X94.592 Y104.575 E.00427
G1 X94.391 Y104.538 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z1.6 F42000
G1 X61.755 Y60.52 Z1.6
G1 Z1.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X117.924 Y104.273 E.04862
G1 X117.924 Y121.241 E.56286
G1 X109.984 Y121.241 E.26338
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.331 Y104.244 E.04862
G1 X118.331 Y121.523 E.57318
G1 X118.29 Y121.648 E.00437
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.723 Y104.216 E.04504
G1 X118.723 Y121.586 E.53374
G1 X118.573 Y122.04 E.01469
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
M73 P42 R14
G1 E-.04 F1800
M204 S10000
G17
G3 Z1.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z1.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z1.6 F4000
            G39.3 S1
            G0 Z1.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z1.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z1.6 F42000
G1 X61.959 Y60.25 Z1.6
G1 Z1.2
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.065 Y103.04 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
; LINE_WIDTH: 0.106791
G1 F15000
M204 S6000
G1 X111.954 Y102.911 E.00089
; LINE_WIDTH: 0.133124
G1 X111.82 Y102.777 E.00139
M204 S10000
G1 X111.156 Y102.613 F42000
; LINE_WIDTH: 0.429405
G1 F9314.731
M204 S6000
G2 X110.932 Y102.557 I-.931 J3.235 E.00728
; LINE_WIDTH: 0.395101
G1 F10222.036
G1 X110.814 Y102.535 E.00343
; LINE_WIDTH: 0.352095
G1 F11643.907
G1 X110.696 Y102.514 E.00301
; LINE_WIDTH: 0.309089
G1 F13525.255
G1 X110.579 Y102.492 E.0026
; LINE_WIDTH: 0.263553
G1 F15000
G1 X110.447 Y102.469 E.00241
; LINE_WIDTH: 0.223079
G1 X110.289 Y102.451 E.00233
; LINE_WIDTH: 0.188391
G1 X110.131 Y102.434 E.00188
; LINE_WIDTH: 0.152988
G1 X109.966 Y102.416 E.00149
; LINE_WIDTH: 0.116851
G1 X109.495 Y102.398 E.00284
G2 X109.003 Y102.415 I-.013 J6.961 E.00296
; LINE_WIDTH: 0.157665
G1 X108.768 Y102.44 E.00221
; LINE_WIDTH: 0.207209
G1 X108.533 Y102.464 E.00317
; LINE_WIDTH: 0.233904
G1 X108.519 Y102.466 E.00021
; LINE_WIDTH: 0.256953
G1 X108.401 Y102.487 E.0021
; LINE_WIDTH: 0.299201
G1 F14047.117
G1 X108.282 Y102.508 E.00252
; LINE_WIDTH: 0.341449
G1 F12059.162
G1 X108.164 Y102.53 E.00293
; LINE_WIDTH: 0.383696
G1 F10564.122
G1 X108.045 Y102.551 E.00334
; LINE_WIDTH: 0.422657
G1 F9480.244
G2 X107.798 Y102.612 I.739 J3.495 E.00787
M204 S10000
G1 X107.132 Y102.777 F42000
; LINE_WIDTH: 0.119354
G1 F15000
M204 S6000
G1 X106.897 Y103.029 E.00215
; WIPE_START
G1 X107.132 Y102.777 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X101.089 Y103.372 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X101.406 Y103.94 E.01997
G3 X101.632 Y106.957 I-4.112 J1.824 E.0948
G3 X101.089 Y108.128 I-4.073 J-1.176 E.03981
G1 X105.862 Y108.128 E.14667
G1 X105.536 Y107.543 E.02058
G3 X105.185 Y105.217 I3.907 J-1.779 E.07323
G1 X105.323 Y104.53 E.02152
G3 X105.851 Y103.383 I4.195 J1.238 E.03894
G1 X101.149 Y103.372 E.14449
M204 S10000
G1 X101.732 Y103.749 F42000
G1 F9547.299
M204 S6000
G1 X101.977 Y104.386 E.02095
G1 X102.126 Y105.041 E.02063
G3 X102 Y107.037 I-5.314 J.668 E.06182
G2 X101.743 Y107.751 I14.569 J5.65 E.02331
G1 X105.219 Y107.751 E.10681
G1 X104.968 Y107.099 E.02145
G1 X104.821 Y106.429 E.02109
G3 X104.955 Y104.448 I5.281 J-.637 E.06136
G1 X105.218 Y103.75 E.02294
G1 X101.792 Y103.749 E.10526
M204 S10000
G1 X102.283 Y104.127 F42000
G1 F9547.299
M204 S6000
G1 X102.494 Y104.96 E.02643
G1 X102.553 Y105.656 E.02146
G1 X102.518 Y106.346 E.02121
G1 X102.368 Y107.117 E.02414
G1 X102.283 Y107.373 E.00831
G1 X104.668 Y107.373 E.07327
G1 X104.452 Y106.507 E.02744
G3 X104.587 Y104.366 I5.684 J-.716 E.06629
G1 X104.667 Y104.127 E.00777
G1 X102.343 Y104.127 E.07141
M204 S10000
G1 X102.781 Y104.504 F42000
G1 F9547.299
M204 S6000
G3 X102.781 Y106.996 I-5.099 J1.246 E.07733
G1 X104.17 Y106.996 E.04269
G3 X104.17 Y104.504 I5.131 J-1.247 E.07732
G1 X102.841 Y104.504 E.04084
M204 S10000
G1 X103.253 Y104.89 F42000
; LINE_WIDTH: 0.424105
G1 F9444.234
M204 S6000
G3 X103.252 Y106.611 I-9.749 J.858 E.05354
G1 X103.698 Y106.611 E.01386
G3 X103.697 Y104.89 I9.655 J-.866 E.05354
G1 X103.313 Y104.89 E.01195
; WIPE_START
G1 X103.697 Y104.89 E-.14618
G1 X103.672 Y105.102 E-.08123
G1 X103.654 Y105.871 E-.29238
G1 X103.692 Y106.502 E-.24021
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z1.6 F42000
G1 Z1.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108298
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134108
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.426441
G1 F9386.713
M204 S6000
G2 X98.92 Y102.554 I-.945 J3.267 E.00755
; LINE_WIDTH: 0.389902
G1 F10375.197
G1 X98.802 Y102.533 E.00341
; LINE_WIDTH: 0.347113
G1 F11834.615
G1 X98.683 Y102.511 E.00299
; LINE_WIDTH: 0.304324
G1 F13771.815
G1 X98.564 Y102.49 E.00257
; LINE_WIDTH: 0.259087
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219141
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185157
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150488
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.116351
G1 X97.473 Y102.398 E.00286
G2 X96.992 Y102.415 I-.003 J6.555 E.00288
; LINE_WIDTH: 0.151159
G1 X96.834 Y102.432 E.0014
; LINE_WIDTH: 0.185143
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.220675
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.261542
G1 X96.385 Y102.49 E.00215
; LINE_WIDTH: 0.304341
G1 F13770.89
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347141
G1 F11833.518
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.389941
G1 F10374.036
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426472
G1 F9385.959
G2 X95.796 Y102.613 I.709 J3.319 E.00755
M204 S10000
G1 X94.732 Y103.84 F42000
; LINE_WIDTH: 0.106643
G1 F15000
M204 S6000
G1 X94.649 Y103.937 E.00067
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497433
G1 F7920.564
M204 S6000
G1 X94.419 Y105.024 E.00999
; LINE_WIDTH: 0.463243
G1 F8564.85
G2 X94.389 Y105.321 I4.137 J.58 E.01023
; LINE_WIDTH: 0.429914
G1 F9302.473
G2 X94.391 Y106.208 I8.941 J.423 E.028
; LINE_WIDTH: 0.465
G1 F8529.204
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.497413
G1 F7920.912
G1 X94.448 Y106.744 E.00999
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.106661
G1 F15000
M204 S6000
G2 X94.649 Y107.564 I.126 J.005 E.00052
G1 X94.732 Y107.661 E.00067
M204 S10000
G1 X95.796 Y108.887 F42000
; LINE_WIDTH: 0.426482
G1 F9385.718
M204 S6000
G2 X96.03 Y108.946 I.957 J-3.317 E.00755
; LINE_WIDTH: 0.389976
G1 F10372.98
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.347171
G1 F11832.331
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304367
G1 F13769.539
G1 X96.386 Y109.01 E.00257
; LINE_WIDTH: 0.261563
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.220702
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185159
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.15116
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.11637
G2 X97.473 Y109.102 I.487 J-6.816 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.150499
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185183
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219181
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259135
G1 X98.565 Y109.01 E.00237
; LINE_WIDTH: 0.304347
G1 F13770.618
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.347112
G1 F11834.643
G1 X98.802 Y108.967 E.00299
; LINE_WIDTH: 0.389878
G1 F10375.919
G1 X98.92 Y108.946 E.00341
; LINE_WIDTH: 0.426423
G1 F9387.171
G2 X99.154 Y108.887 I-.71 J-3.321 E.00755
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.134073
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.108277
G1 X100.065 Y108.46 E.001
; WIPE_START
G1 X99.942 Y108.601 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.57 Y108.879 Z1.6 F42000
G1 X107.794 Y108.887 Z1.6
G1 Z1.2
G1 E.8 F1800
; LINE_WIDTH: 0.430151
G1 F9296.785
M204 S6000
G2 X108.015 Y108.943 I.933 J-3.243 E.00719
; LINE_WIDTH: 0.396526
G1 F10180.82
G1 X108.132 Y108.964 E.00342
; LINE_WIDTH: 0.353868
G1 F11577.527
G1 X108.248 Y108.985 E.00301
; LINE_WIDTH: 0.311209
G1 F13418.398
G1 X108.365 Y109.007 E.0026
; LINE_WIDTH: 0.26855
G1 F15000
G1 X108.482 Y109.028 E.00218
; LINE_WIDTH: 0.221846
G1 X108.696 Y109.053 E.00315
; LINE_WIDTH: 0.181957
G1 X108.839 Y109.068 E.00163
; LINE_WIDTH: 0.151337
G1 X108.981 Y109.084 E.00126
; LINE_WIDTH: 0.116272
G2 X109.458 Y109.102 I.498 J-6.744 E.00285
G1 X109.93 Y109.086 E.00282
; LINE_WIDTH: 0.147936
G1 X110.097 Y109.069 E.00144
; LINE_WIDTH: 0.182445
G1 X110.259 Y109.052 E.00185
; LINE_WIDTH: 0.216308
G1 X110.421 Y109.035 E.0023
; LINE_WIDTH: 0.245797
G1 X110.595 Y109.005 E.00292
; WIPE_START
G1 X110.421 Y109.035 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.43 Y116.049 Z1.6 F42000
G1 X113.954 Y117.271 Z1.6
G1 Z1.2
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.60844
G1 F6365.823
M204 S6000
G1 X113.954 Y110.766 E.29975
M204 S10000
G1 X113.483 Y110.491 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X113.483 Y117.742 E.2228
G1 X114.425 Y117.742 E.02896
G1 X114.425 Y109.488 E.25361
G3 X113.528 Y110.452 I-5.687 J-4.394 E.04051
M204 S10000
G1 X114.802 Y108.126 F42000
G1 F9547.299
M204 S6000
G1 X114.434 Y108.823 E.02425
G1 X113.949 Y109.494 E.02542
G1 X113.358 Y110.103 E.02608
G1 X113.106 Y110.311 E.01005
G1 X113.106 Y118.119 E.23992
G1 X114.802 Y118.119 E.05213
G1 X114.802 Y108.186 E.30523
M204 S10000
G1 X114.774 Y104.499 F42000
; LINE_WIDTH: 0.39259
G1 F10295.421
M204 S6000
G1 X114.87 Y105.102 E.01742
; LINE_WIDTH: 0.366083
G1 F11139.895
G3 X114.866 Y106.451 I-7.133 J.649 E.03556
; LINE_WIDTH: 0.419071
G1 F9570.635
G1 X114.727 Y107.231 E.02428
G1 X114.468 Y107.953 E.02351
G1 X114.103 Y108.641 E.02388
G1 X113.648 Y109.266 E.02371
G1 X113.093 Y109.835 E.02435
G1 X112.729 Y110.121 E.0142
G1 X112.729 Y118.496 E.25671
G1 X115.18 Y118.496 E.07512
G1 X115.18 Y107.281 E.34378
G1 X115.193 Y106.676 E.01855
; LINE_WIDTH: 0.369881
G1 F11010.511
G2 X115.202 Y105.091 I-22.523 J-.919 E.04222
; LINE_WIDTH: 0.399166
G1 F10105.391
G1 X115.184 Y104.499 E.01721
G1 X114.834 Y104.499 E.01017
M204 S10000
G1 X114.282 Y104.127 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G3 X112.352 Y109.932 I-4.835 J1.616 E.2016
G1 X112.352 Y118.873 E.27475
G1 X115.557 Y118.873 E.09848
G1 X115.557 Y104.466 E.44269
G1 X115.511 Y104.127 E.01052
G1 X114.342 Y104.127 E.03592
M204 S10000
G1 X113.731 Y103.749 F42000
G1 F9547.299
M204 S6000
G1 X113.981 Y104.401 E.02144
G1 X114.129 Y105.072 E.02113
G3 X113.991 Y107.066 I-5.2 J.64 E.0618
G1 X113.763 Y107.686 E.02029
G1 X113.443 Y108.277 E.02064
G1 X113.046 Y108.812 E.02046
G1 X112.563 Y109.299 E.02109
G3 X111.974 Y109.735 I-3.019 J-3.449 E.02253
G1 X111.974 Y119.251 E.29237
G1 X115.934 Y119.251 E.12165
G1 X115.934 Y104.466 E.45428
G1 X115.838 Y103.749 E.02221
G1 X113.791 Y103.749 E.06291
M204 S10000
G1 X113.086 Y103.372 F42000
G1 F9547.299
M204 S6000
G1 X113.414 Y103.957 E.0206
G3 X111.597 Y109.511 I-3.959 J1.779 E.19698
G1 X111.597 Y119.628 E.31084
G1 X116.311 Y119.628 E.14482
G1 X116.311 Y104.466 E.46586
G1 X116.165 Y103.372 E.0339
G1 X113.146 Y103.372 E.09277
; CHANGE_LAYER
; Z_HEIGHT: 1.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X115.146 Y103.372 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 7/79
; update layer progress
M73 L7
M991 S0 P6 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z1.6 I-.298 J-1.18 P1  F42000
G1 X99.722 Y107.262 Z1.6
G1 Z1.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.527 Y107.528 E.01096
G3 X97.258 Y103.054 I-2.045 J-1.775 E.35165
G3 X99.524 Y103.974 I.213 J2.728 E.08413
M73 P43 R14
G3 X99.761 Y107.216 I-2.042 J1.778 E.11564
M204 S10000
G1 X99.426 Y106.971 F42000
G1 F8843.478
M204 S6000
G1 X99.416 Y106.998 E.00094
G3 X97.287 Y103.46 I-1.934 J-1.246 E.30948
G3 X98.984 Y104.009 I.202 J2.272 E.06078
G3 X99.574 Y106.709 I-1.501 J1.743 E.09834
G1 X99.456 Y106.919 E.008
M204 S250
G1 X99.087 Y106.786 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.315 Y103.851 I-1.603 J-1.035 E.23745
G3 X98.269 Y104.012 I.177 J1.853 E.03007
G3 X99.119 Y106.735 I-.784 J1.739 E.09901
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.1264
G1 X98.726 Y107.194 E-.1036
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10357
G1 X97.747 Y107.641 E-.10357
G1 X97.475 Y107.661 E-.1036
G1 X97.443 Y107.658 E-.01208
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X94.798 Y103.45 I2.056 J3.225 E.03623
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.165 Y103.084 E-.22601
G1 X94.798 Y103.45 E-.19688
G1 X94.798 Y102.573 E-.33322
G1 X94.809 Y102.573 E-.00389
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01719
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07721
G1 X94.798 Y108.927 E-.29242
G1 X94.798 Y108.05 E-.33322
G1 X94.905 Y108.156 E-.05715
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z1.8 F42000
G1 X106.691 Y108.52 Z1.8
G1 Z1.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.2118
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.311 J-2.128 E.14915
G1 X100.306 Y102.98 E.02659
G1 X106.647 Y102.98 E.21036
G1 X106.175 Y103.605 E.02599
G1 X105.907 Y104.089 E.01833
G2 X106.649 Y108.477 I3.579 J1.652 E.15686
; WIPE_START
G1 X104.649 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.621 Y108.76 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.566 Y108.927 E.00583
G1 X99.382 Y108.927 E.27146
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18577
G2 X99.327 Y102.74 I-3.357 J2.283 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.572 Y102.573 E.27165
G1 X107.626 Y102.742 E.00588
G2 X107.155 Y108.407 I1.874 J3.008 E.21883
G1 X107.574 Y108.724 E.01742
; WIPE_START
G1 X107.566 Y108.927 E-.07709
G1 X105.768 Y108.927 E-.68292
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.656 Y108.631 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.342 Y108.747 E.0111
G3 X109.296 Y102.642 I-.86 J-2.995 E.34742
G3 X111.841 Y103.717 I.169 J3.151 E.09484
G3 X110.757 Y108.596 I-2.358 J2.036 E.1924
G1 X110.713 Y108.611 E.00156
M204 S10000
G1 X110.516 Y108.249 F42000
G1 F8843.478
M204 S6000
G1 X110.228 Y108.356 E.01017
G3 X109.322 Y103.049 I-.746 J-2.604 E.30196
G3 X111.261 Y103.71 I.142 J2.758 E.06963
G3 X110.589 Y108.224 I-1.779 J2.042 E.18004
G1 X110.572 Y108.23 E.00059
M204 S10000
G1 X110.375 Y107.867 F42000
G1 F8843.478
M204 S6000
G1 X110.113 Y107.959 E.00923
G3 X109.348 Y103.455 I-.638 J-2.209 E.2568
G3 X110.609 Y103.751 I.122 J2.317 E.04355
G3 X110.43 Y107.841 I-1.134 J1.999 E.16755
M204 S250
G1 X110.24 Y107.499 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.005 Y107.587 E.00773
G3 X109.373 Y103.846 I-.522 J-1.836 E.19706
G3 X110.277 Y104.016 I.118 J1.859 E.02855
G3 X110.296 Y107.478 I-.794 J1.735 E.13323
; WIPE_START
M204 S6000
G1 X110.005 Y107.587 E-.11828
G1 X109.846 Y107.62 E-.06142
G1 X109.465 Y107.66 E-.14569
G1 X109.194 Y107.64 E-.10339
G1 X108.927 Y107.58 E-.10409
G1 X108.672 Y107.484 E-.10329
G1 X108.434 Y107.352 E-.10354
G1 X108.391 Y107.32 E-.02031
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.257 Y102.98 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.14091
G1 X116.741 Y104.624 E.05507
G1 X116.741 Y120.02 E.51071
G1 X111.205 Y120.02 E.18361
G1 X111.205 Y109.277 E.35634
G2 X112.218 Y108.561 I-1.822 J-3.645 E.0413
G1 X112.44 Y108.338 E.01043
G2 X112.299 Y103.023 I-2.961 J-2.581 E.19373
; WIPE_START
G1 X114.299 Y103.003 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.384 Y102.573 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18302
G1 X116.902 Y102.88 E.01018
G1 X117.148 Y104.595 E.05746
G1 X117.148 Y120.427 E.52518
G1 X110.798 Y120.427 E.21062
G1 X110.798 Y109.013 E.37862
G1 X110.924 Y108.967 E.00444
G2 X111.799 Y103.096 I-1.467 J-3.219 E.23361
G1 X111.329 Y102.74 E.01957
G1 X111.365 Y102.63 E.00384
; WIPE_START
G1 X113.365 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.735 Y102.431 Z1.8 F42000
G1 X94.391 Y102.166 Z1.8
G1 Z1.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.555 Y104.566 E.05746
G1 X117.555 Y120.834 E.53964
G1 X110.391 Y120.834 E.23763
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.961 E.0787
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00428
G2 X94.637 Y104.454 I2.837 J-1.296 E.5615
G1 X94.592 Y104.575 E.00427
G1 X94.391 Y104.538 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z1.8 F42000
G1 X61.755 Y60.52 Z1.8
G1 Z1.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X117.962 Y104.537 E.05746
G1 X117.962 Y121.241 E.55411
G1 X109.984 Y121.241 E.26463
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.369 Y104.508 E.05746
G1 X118.369 Y121.408 E.56063
G1 X118.29 Y121.648 E.00837
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.761 Y104.48 E.05322
G1 X118.761 Y121.471 E.52211
G1 X118.573 Y122.04 E.0184
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
M73 P43 R13
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z1.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z1.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z1.8 F4000
            G39.3 S1
            G0 Z1.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z1.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z1.8 F42000
G1 X61.959 Y60.25 Z1.8
G1 Z1.4
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z1.8 F42000
M73 P44 R13
G1 Z1.4
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.392 Y104.854 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.203 Y103.329 E.051
G1 X116.114 Y103.329 E.00296
G3 X114.372 Y104.248 I-1.523 J-.775 E.06965
G3 X113.586 Y103.386 I1.458 J-2.119 E.03905
G1 X113.495 Y103.329 E.00357
G1 X112.999 Y103.329 E.01645
G3 X113.7 Y105.073 I-3.654 J2.482 E.06284
G1 X113.848 Y105.103 E.005
G3 X114.634 Y105.965 I-1.458 J2.119 E.03905
G1 X115.158 Y106.296 E.02057
G2 X116.392 Y105.906 I.406 J-.862 E.04722
G1 X116.392 Y107.259 E.0449
G2 X115.682 Y108.062 I1.367 J1.926 E.03586
G3 X114.372 Y108.442 I-1.042 J-1.145 E.04687
G3 X113.586 Y107.579 I1.458 J-2.119 E.03905
G1 X113.398 Y107.46 E.00738
G3 X111.554 Y109.485 I-3.793 J-1.602 E.09262
G1 X111.554 Y110.578 E.03625
G1 X111.751 Y110.538 E.00669
G2 X112.537 Y109.676 I-1.458 J-2.119 E.03905
G3 X113.848 Y109.296 I1.042 J1.145 E.04687
G3 X114.634 Y110.158 I-1.458 J2.119 E.03905
G1 X115.158 Y110.49 E.02057
G2 X116.392 Y110.099 I.406 J-.862 E.04722
G1 X116.392 Y111.452 E.0449
G2 X115.682 Y112.255 I1.367 J1.926 E.03586
G3 X114.372 Y112.635 I-1.042 J-1.145 E.04687
G3 X113.586 Y111.772 I1.458 J-2.119 E.03905
G2 X112.275 Y111.392 I-1.042 J1.145 E.04687
G2 X111.554 Y112.174 I1.318 J1.94 E.03561
G1 X111.554 Y114.771 E.08614
G1 X111.751 Y114.731 E.00669
G2 X112.537 Y113.869 I-1.458 J-2.119 E.03905
G3 X113.848 Y113.489 I1.042 J1.145 E.04687
G3 X114.634 Y114.351 I-1.458 J2.119 E.03905
G1 X115.158 Y114.683 E.02057
G2 X116.392 Y114.292 I.406 J-.862 E.04722
G1 X116.392 Y115.645 E.0449
G2 X115.682 Y116.448 I1.368 J1.926 E.03586
G3 X114.372 Y116.828 I-1.042 J-1.145 E.04687
G3 X113.586 Y115.965 I1.458 J-2.119 E.03905
G2 X112.275 Y115.585 I-1.042 J1.145 E.04687
G2 X111.554 Y116.367 I1.318 J1.941 E.03561
G1 X111.554 Y118.964 E.08614
G1 X111.751 Y118.924 E.00669
G2 X112.537 Y118.062 I-1.458 J-2.119 E.03905
G3 X113.848 Y117.682 I1.042 J1.145 E.04687
G3 X114.634 Y118.544 I-1.458 J2.119 E.03905
G1 X115.158 Y118.876 E.02057
G2 X116.392 Y118.485 I.406 J-.862 E.04722
G1 X116.392 Y119.672 E.03937
G1 X115.951 Y119.672 E.01465
; WIPE_START
G1 X116.392 Y119.672 E-.16779
G1 X116.392 Y118.485 E-.45097
G1 X116.127 Y118.745 E-.14124
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.263 Y112.163 Z1.8 F42000
G1 X106.899 Y103.027 Z1.8
G1 Z1.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.119091
G1 F15000
M204 S6000
G1 X107.133 Y102.777 E.00212
M204 S10000
G1 X107.798 Y102.612 F42000
; LINE_WIDTH: 0.422023
G1 F9496.121
M204 S6000
G3 X108.048 Y102.55 I1.006 J3.515 E.00794
; LINE_WIDTH: 0.382564
G1 F10599.355
G1 X108.166 Y102.529 E.00333
; LINE_WIDTH: 0.34041
G1 F12101.248
G1 X108.285 Y102.508 E.00292
; LINE_WIDTH: 0.298257
G1 F14099.034
G1 X108.403 Y102.487 E.00251
; LINE_WIDTH: 0.256104
G1 F15000
G1 X108.522 Y102.466 E.00209
; LINE_WIDTH: 0.233121
G1 X108.536 Y102.464 E.00021
; LINE_WIDTH: 0.206554
G1 X108.771 Y102.439 E.00315
; LINE_WIDTH: 0.157261
G1 X109.005 Y102.415 E.0022
; LINE_WIDTH: 0.116857
G3 X109.497 Y102.398 I.473 J6.838 E.00296
G1 X109.969 Y102.416 E.00285
; LINE_WIDTH: 0.153428
G1 X110.133 Y102.434 E.00149
; LINE_WIDTH: 0.188968
G1 X110.291 Y102.451 E.00189
; LINE_WIDTH: 0.223786
G1 X110.449 Y102.469 E.00234
; LINE_WIDTH: 0.264361
G1 X110.581 Y102.493 E.00242
; LINE_WIDTH: 0.309966
G1 F13480.842
G1 X110.699 Y102.514 E.0026
; LINE_WIDTH: 0.353023
G1 F11609.057
G1 X110.816 Y102.536 E.00302
; LINE_WIDTH: 0.39608
G1 F10193.686
G1 X110.934 Y102.557 E.00344
; LINE_WIDTH: 0.429963
G1 F9301.289
G3 X111.156 Y102.613 I-.709 J3.299 E.00723
; WIPE_START
G1 X110.934 Y102.557 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.595 Y109.005 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
; LINE_WIDTH: 0.245561
G1 F15000
M204 S6000
G1 X110.419 Y109.035 E.00295
; LINE_WIDTH: 0.215812
G1 X110.257 Y109.052 E.00229
; LINE_WIDTH: 0.181996
G1 X110.095 Y109.069 E.00184
; LINE_WIDTH: 0.147537
G1 X109.927 Y109.087 E.00144
; LINE_WIDTH: 0.116275
G1 X109.456 Y109.102 E.00282
G3 X108.979 Y109.084 I.037 J-7.114 E.00285
; LINE_WIDTH: 0.1508
G1 X108.845 Y109.069 E.00118
; LINE_WIDTH: 0.179741
G1 X108.71 Y109.055 E.00151
; LINE_WIDTH: 0.218965
G1 X108.494 Y109.03 E.00313
; LINE_WIDTH: 0.245696
G1 X108.48 Y109.028 E.00023
; LINE_WIDTH: 0.269174
G1 X108.363 Y109.006 E.00219
; LINE_WIDTH: 0.31204
G1 F13376.964
G1 X108.246 Y108.985 E.00261
; LINE_WIDTH: 0.354906
G1 F11538.994
G1 X108.129 Y108.964 E.00303
; LINE_WIDTH: 0.397772
G1 F10145.081
G1 X108.012 Y108.942 E.00344
; LINE_WIDTH: 0.430909
G1 F9278.623
G3 X107.794 Y108.887 I.667 J-3.093 E.00711
; WIPE_START
G1 X108.012 Y108.942 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.366 Y106.959 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X105.95 Y108.172 I4.541 J-1.44 E.04479
G1 X105.673 Y108.172 E.00917
G2 X104.151 Y107.146 I-1.762 J.974 E.06319
G2 X103.627 Y107.406 I-.006 J.647 E.02013
G1 X103.103 Y108.062 E.02785
G1 X102.929 Y108.172 E.00682
G1 X101.48 Y108.172 E.04807
G1 X101.208 Y107.831 E.01444
G2 X101.748 Y105.581 I-3.766 J-2.093 E.07772
G2 X103.365 Y106.345 I1.35 J-.764 E.06323
G2 X104.151 Y105.483 I-1.458 J-2.119 E.03905
G3 X105.25 Y105.06 I1.18 J1.43 E.03972
G3 X105.613 Y103.903 I5.462 J1.076 E.04032
G1 X105.109 Y103.329 E.02533
G1 X103.535 Y103.329 E.05221
G3 X101.793 Y104.248 I-1.523 J-.775 E.06965
G3 X101.001 Y103.329 I3.325 J-3.661 E.04036
G1 X102.339 Y103.329 E.04438
; WIPE_START
G1 X101.001 Y103.329 E-.50844
G1 X101.396 Y103.86 E-.25156
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z1.8 F42000
G1 Z1.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.1083
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134102
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.42644
G1 F9386.73
M204 S6000
G2 X98.92 Y102.554 I-.949 J3.284 E.00755
; LINE_WIDTH: 0.389902
G1 F10375.197
G1 X98.802 Y102.533 E.00341
; LINE_WIDTH: 0.347113
G1 F11834.615
G1 X98.683 Y102.511 E.00299
; LINE_WIDTH: 0.304324
G1 F13771.815
G1 X98.564 Y102.49 E.00257
; LINE_WIDTH: 0.259089
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219145
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185159
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150487
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.116351
G1 X97.473 Y102.398 E.00286
G2 X96.992 Y102.415 I-.003 J6.555 E.00288
; LINE_WIDTH: 0.151156
G1 X96.834 Y102.432 E.0014
; LINE_WIDTH: 0.185133
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.220657
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.261509
G1 X96.386 Y102.49 E.00215
; LINE_WIDTH: 0.304318
G1 F13772.122
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347127
G1 F11834.064
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.389936
G1 F10374.176
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426473
G1 F9385.933
G2 X95.796 Y102.613 I.714 J3.342 E.00755
M204 S10000
G1 X94.732 Y103.84 F42000
; LINE_WIDTH: 0.106651
G1 F15000
M204 S6000
G1 X94.649 Y103.936 E.00067
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497435
G1 F7920.54
M204 S6000
G1 X94.419 Y105.024 E.00999
; LINE_WIDTH: 0.46323
G1 F8565.105
G2 X94.389 Y105.321 I4.137 J.58 E.01023
; LINE_WIDTH: 0.429914
G1 F9302.468
G2 X94.391 Y106.208 I8.944 J.423 E.028
; LINE_WIDTH: 0.464998
G1 F8529.241
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.4974
G1 F7921.155
G1 X94.448 Y106.744 E.00998
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.106655
G1 F15000
M204 S6000
G2 X94.649 Y107.564 I.126 J.005 E.00052
G1 X94.732 Y107.661 E.00067
M204 S10000
G1 X95.796 Y108.887 F42000
; LINE_WIDTH: 0.426432
G1 F9386.949
M204 S6000
G2 X96.03 Y108.946 I.939 J-3.242 E.00755
; LINE_WIDTH: 0.389895
G1 F10375.413
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.347119
G1 F11834.371
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304344
G1 F13770.774
G1 X96.385 Y109.01 E.00257
; LINE_WIDTH: 0.261568
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.220727
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185189
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.151196
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.116375
G2 X97.473 Y109.102 I.477 J-6.534 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.1505
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185183
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219181
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259129
G1 X98.564 Y109.01 E.00237
; LINE_WIDTH: 0.304342
G1 F13770.848
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.347109
G1 F11834.744
G1 X98.802 Y108.967 E.00299
; LINE_WIDTH: 0.389877
G1 F10375.943
G1 X98.92 Y108.946 E.00341
; LINE_WIDTH: 0.426419
G1 F9387.26
G2 X99.154 Y108.887 I-.72 J-3.366 E.00755
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.134096
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.108278
G1 X100.065 Y108.46 E.001
; CHANGE_LAYER
; Z_HEIGHT: 1.6
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F15000
G1 X99.942 Y108.601 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 8/79
; update layer progress
M73 L8
M991 S0 P7 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z1.8 I1.21 J-.134 P1  F42000
G1 X99.784 Y107.166 Z1.8
G1 Z1.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.76 Y107.219 E.00191
G3 X97.273 Y103.053 I-2.278 J-1.465 E.36509
G3 X99.524 Y103.974 I.198 J2.728 E.08363
G3 X99.946 Y106.878 I-2.042 J1.779 E.10287
G1 X99.813 Y107.114 E.00897
M204 S10000
G1 X99.426 Y106.971 F42000
G1 F8843.478
M204 S6000
G1 X99.416 Y106.997 E.00094
G3 X97.302 Y103.459 I-1.933 J-1.246 E.30985
G3 X98.984 Y104.009 I.187 J2.272 E.06028
G3 X99.574 Y106.709 I-1.501 J1.743 E.09833
G1 X99.456 Y106.919 E.008
M204 S250
G1 X99.085 Y106.785 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.33 Y103.85 I-1.603 J-1.034 E.2379
G3 X98.508 Y104.143 I.142 J1.944 E.03793
G3 X99.117 Y106.734 I-1.025 J1.608 E.09053
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.12637
G1 X98.726 Y107.194 E-.1036
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10357
G1 X97.747 Y107.641 E-.10357
G1 X97.475 Y107.661 E-.1036
G1 X97.443 Y107.658 E-.01212
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z2 F42000
G1 Z1.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X94.798 Y103.45 I2.056 J3.225 E.03623
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.165 Y103.084 E-.22604
G1 X94.798 Y103.45 E-.19685
G1 X94.798 Y102.573 E-.33322
G1 X94.809 Y102.573 E-.0039
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z2 F42000
G1 Z1.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01719
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29243
G1 X94.798 Y108.05 E-.33323
G1 X94.905 Y108.156 E-.05713
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z2 F42000
G1 X106.691 Y108.52 Z2
G1 Z1.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21181
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.311 J-2.128 E.14916
G1 X100.306 Y102.98 E.02659
G1 X106.648 Y102.98 E.21038
G1 X106.177 Y103.602 E.02589
G1 X105.908 Y104.087 E.01836
G2 X106.649 Y108.477 I3.579 J1.654 E.15694
; WIPE_START
G1 X104.649 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.621 Y108.76 Z2 F42000
G1 Z1.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.565 Y108.927 E.00582
G1 X99.382 Y108.927 E.27145
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18578
G2 X99.327 Y102.74 I-3.356 J2.282 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.572 Y102.573 E.27166
G1 X107.627 Y102.742 E.00588
G2 X107.153 Y108.406 I1.874 J3.008 E.21876
G1 X107.573 Y108.724 E.01749
; WIPE_START
G1 X107.565 Y108.927 E-.07707
G1 X105.768 Y108.927 E-.68293
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.648 Y108.634 Z2 F42000
G1 Z1.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.34 Y108.748 E.0109
G3 X109.282 Y102.643 I-.858 J-2.995 E.3469
G3 X111.842 Y103.718 I.183 J3.15 E.09536
G3 X110.755 Y108.597 I-2.36 J2.035 E.19242
G1 X110.705 Y108.614 E.00174
M204 S10000
G1 X110.508 Y108.252 F42000
G1 F8843.478
M204 S6000
G1 X110.226 Y108.356 E.00997
G3 X109.308 Y103.05 I-.744 J-2.604 E.30144
G3 X111.263 Y103.711 I.156 J2.756 E.07016
G3 X110.587 Y108.225 I-1.78 J2.041 E.18004
G1 X110.565 Y108.232 E.00078
M204 S10000
G1 X110.369 Y107.87 F42000
G1 F8843.478
M204 S6000
G1 X110.111 Y107.959 E.00904
G3 X109.335 Y103.456 I-.636 J-2.209 E.25631
G3 X110.597 Y103.744 I.136 J2.313 E.04352
G3 X110.423 Y107.845 I-1.122 J2.007 E.16828
M204 S250
G1 X110.234 Y107.502 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.003 Y107.587 E.00756
G3 X109.36 Y103.847 I-.52 J-1.836 E.19659
G3 X110.278 Y104.017 I.132 J1.858 E.02901
G3 X110.29 Y107.481 I-.795 J1.735 E.13341
; WIPE_START
M204 S6000
G1 X110.003 Y107.587 E-.11615
G1 X109.86 Y107.617 E-.05565
G1 X109.464 Y107.66 E-.15147
G1 X109.192 Y107.639 E-.10336
G1 X108.925 Y107.58 E-.10408
G1 X108.671 Y107.483 E-.1033
G1 X108.433 Y107.351 E-.10358
G1 X108.386 Y107.315 E-.02242
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.258 Y102.98 Z2 F42000
G1 Z1.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.14088
G1 X116.778 Y104.888 E.06391
G1 X116.778 Y120.02 E.50196
G1 X111.205 Y120.02 E.18487
G1 X111.205 Y109.277 E.35635
G2 X112.227 Y108.551 I-1.817 J-3.639 E.04175
G1 X112.438 Y108.34 E.0099
G2 X112.3 Y103.023 I-2.965 J-2.583 E.19375
; WIPE_START
G1 X114.3 Y103.003 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.385 Y102.573 Z2 F42000
G1 Z1.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.183
G1 X116.902 Y102.88 E.01018
G1 X117.186 Y104.859 E.0663
G1 X117.186 Y120.427 E.51643
G1 X110.798 Y120.427 E.21188
G1 X110.798 Y109.013 E.37862
G1 X110.921 Y108.968 E.00435
G2 X111.801 Y103.098 I-1.464 J-3.22 E.2336
G1 X111.329 Y102.74 E.01966
G1 X111.366 Y102.63 E.00383
; WIPE_START
G1 X113.366 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.735 Y102.431 Z2 F42000
G1 X94.391 Y102.166 Z2
G1 Z1.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.593 Y104.83 E.0663
G1 X117.593 Y120.834 E.53089
G1 X110.391 Y120.834 E.23888
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.961 E.0787
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00428
G2 X94.637 Y104.454 I2.834 J-1.296 E.56078
G1 X94.592 Y104.575 E.00427
G1 X94.391 Y104.538 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z2 F42000
G1 X61.755 Y60.52 Z2
G1 Z1.6
M73 P45 R13
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X118 Y104.8 E.0663
G1 X118 Y121.241 E.54536
G1 X109.984 Y121.241 E.26589
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.407 Y104.771 E.0663
G1 X118.407 Y121.294 E.54808
G1 X118.29 Y121.648 E.01237
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.799 Y104.743 E.06141
G1 X118.799 Y121.357 E.51048
G1 X118.573 Y122.04 E.02211
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z2 F4000
            G39.3 S1
            G0 Z2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z1.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z2 F42000
G1 X61.959 Y60.25 Z2
G1 Z1.6
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z2 F42000
G1 Z1.6
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.384 Y104.592 Z2 F42000
G1 Z1.6
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G3 X116.364 Y106.51 I-9.151 J.863 E.06374
G1 X116.43 Y106.667 E.00566
G1 X116.43 Y110.41 E.12415
G2 X116.43 Y110.86 I.574 J.225 E.01529
G1 X116.43 Y114.603 E.12415
G2 X116.43 Y115.054 I.574 J.225 E.01529
G1 X116.43 Y118.796 E.12415
G2 X116.43 Y119.247 I.574 J.225 E.01529
M73 P46 R13
G1 X116.43 Y119.672 E.0141
G1 X116.037 Y119.672 E.01305
G2 X115.939 Y119.351 I-.283 J-.088 E.01181
G1 X114.973 Y118.827 E.03644
G3 X114.268 Y117.517 I1.683 J-1.751 E.05018
G1 X114.378 Y117.255 E.00943
G1 X115.343 Y116.731 E.03644
G2 X116.049 Y115.42 I-1.683 J-1.752 E.05018
G1 X115.939 Y115.158 E.00943
G1 X114.973 Y114.634 E.03644
G3 X114.268 Y113.324 I1.683 J-1.751 E.05018
G1 X114.378 Y113.062 E.00943
G1 X115.343 Y112.538 E.03644
G2 X116.049 Y111.227 I-1.683 J-1.752 E.05017
G1 X115.939 Y110.965 E.00943
G1 X114.973 Y110.441 E.03644
G3 X114.268 Y109.131 I1.683 J-1.751 E.05017
G1 X114.378 Y108.869 E.00943
G1 X115.343 Y108.344 E.03644
G2 X116.049 Y107.034 I-1.683 J-1.752 E.05018
G1 X115.939 Y106.772 E.00943
G1 X114.973 Y106.248 E.03644
G3 X114.268 Y104.938 I1.683 J-1.751 E.05018
G1 X114.378 Y104.676 E.00943
G1 X115.343 Y104.151 E.03644
G2 X115.904 Y103.329 I-.986 J-1.274 E.03358
G1 X113.436 Y103.329 E.08187
G3 X113.952 Y104.414 I-1.695 J1.472 E.04035
G3 X113.64 Y104.785 I-.388 J-.009 E.0174
G3 X113.393 Y107.471 I-4.033 J.984 E.09112
G3 X113.952 Y108.607 I-1.674 J1.529 E.04254
G1 X113.842 Y108.869 E.00943
G1 X112.877 Y109.393 E.03644
G2 X112.171 Y110.703 I1.683 J1.751 E.05018
G1 X112.281 Y110.965 E.00943
G1 X113.247 Y111.489 E.03644
G3 X113.952 Y112.8 I-1.683 J1.751 E.05018
G1 X113.842 Y113.062 E.00943
G1 X112.877 Y113.586 E.03644
G2 X112.171 Y114.896 I1.683 J1.751 E.05018
G1 X112.281 Y115.158 E.00943
G1 X113.247 Y115.682 E.03644
G3 X113.952 Y116.993 I-1.683 J1.751 E.05017
G1 X113.842 Y117.255 E.00943
G1 X112.877 Y117.779 E.03644
G2 X112.171 Y119.089 I1.683 J1.751 E.05017
G1 X112.281 Y119.351 E.00943
G1 X112.871 Y119.672 E.02226
G1 X111.844 Y119.672 E.03408
G2 X111.554 Y119.222 I-.524 J.02 E.01862
G1 X111.59 Y116.206 E.10005
G2 X111.856 Y115.42 I-2.001 J-1.114 E.02768
G2 X111.554 Y115.029 I-.449 J.034 E.01735
G1 X111.59 Y112.013 E.10005
G2 X111.856 Y111.227 I-2.001 J-1.114 E.02768
G2 X111.554 Y110.836 I-.449 J.034 E.01735
G1 X111.554 Y109.485 E.04482
G2 X111.795 Y109.35 I-.349 J-.907 E.00922
; WIPE_START
G1 X111.554 Y109.485 E-.10526
G1 X111.554 Y110.836 E-.5134
G1 X111.745 Y110.965 E-.08786
G1 X111.8 Y111.095 E-.05348
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.595 Y109.005 Z2 F42000
G1 Z1.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.24533
G1 F15000
M204 S6000
G1 X110.416 Y109.036 E.00298
; LINE_WIDTH: 0.215301
G1 X110.255 Y109.053 E.00228
; LINE_WIDTH: 0.181581
G1 X110.093 Y109.069 E.00183
; LINE_WIDTH: 0.147218
G1 X109.926 Y109.087 E.00143
; LINE_WIDTH: 0.1163
G1 X109.453 Y109.102 E.00283
G3 X108.977 Y109.083 I.029 J-6.826 E.00285
; LINE_WIDTH: 0.150316
G1 X108.851 Y109.07 E.00111
; LINE_WIDTH: 0.177571
G1 X108.724 Y109.056 E.0014
; LINE_WIDTH: 0.204503
G1 X108.608 Y109.043 E.00154
; LINE_WIDTH: 0.23262
G1 X108.478 Y109.028 E.00202
; LINE_WIDTH: 0.269834
G1 X108.361 Y109.006 E.0022
; LINE_WIDTH: 0.31282
G1 F13338.302
G1 X108.244 Y108.985 E.00262
; LINE_WIDTH: 0.355806
G1 F11505.801
G1 X108.126 Y108.963 E.00304
; LINE_WIDTH: 0.398792
G1 F10115.999
G1 X108.009 Y108.942 E.00345
; LINE_WIDTH: 0.431333
G1 F9268.482
G1 X107.982 Y108.936 E.00087
G1 X107.869 Y108.661 E.0094
; WIPE_START
G1 X107.982 Y108.936 E-.69545
G1 X108.009 Y108.942 E-.06455
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.445 Y107.176 Z2 F42000
G1 Z1.6
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X105.95 Y108.172 I4.215 J-1.51 E.03712
G1 X105.443 Y108.172 E.01683
G2 X104.86 Y107.296 I-1.638 J.458 E.03545
G1 X103.895 Y106.772 E.03644
G1 X103.785 Y106.51 E.00943
G3 X104.491 Y105.2 I2.388 J.441 E.05018
G1 X105.319 Y104.75 E.03126
G3 X105.512 Y104.15 I2.178 J.369 E.02098
G2 X105.05 Y103.329 I-1.495 J.3 E.03178
G1 X103.325 Y103.329 E.05722
G3 X102.764 Y104.151 I-1.547 J-.452 E.03358
G1 X101.799 Y104.676 E.03644
G1 X101.689 Y104.938 E.00943
G2 X102.394 Y106.248 I2.388 J-.441 E.05018
G1 X103.359 Y106.772 E.03644
G1 X103.47 Y107.034 E.00943
G3 X102.909 Y108.172 I-2.234 J-.394 E.04263
G1 X101.281 Y108.172 E.05401
; WIPE_START
G1 X102.909 Y108.172 E-.61876
G1 X103.148 Y107.887 E-.14124
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y108.46 Z2 F42000
G1 Z1.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108282
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.001
; LINE_WIDTH: 0.134098
G1 X99.82 Y108.723 E.00128
M204 S10000
G1 X99.154 Y108.887 F42000
; LINE_WIDTH: 0.426419
G1 F9387.263
M204 S6000
G3 X98.92 Y108.946 I-.948 J-3.281 E.00755
; LINE_WIDTH: 0.389877
G1 F10375.943
G1 X98.802 Y108.967 E.00341
; LINE_WIDTH: 0.347109
G1 F11834.744
G1 X98.683 Y108.989 E.00299
; LINE_WIDTH: 0.304342
G1 F13770.848
G1 X98.564 Y109.01 E.00257
; LINE_WIDTH: 0.259129
G1 F15000
G1 X98.432 Y109.034 E.00237
; LINE_WIDTH: 0.219181
G1 X98.274 Y109.051 E.00228
; LINE_WIDTH: 0.185183
G1 X98.116 Y109.068 E.00184
; LINE_WIDTH: 0.1505
G1 X97.951 Y109.085 E.00145
; LINE_WIDTH: 0.116371
G1 X97.473 Y109.102 E.00286
G3 X96.992 Y109.085 I.007 J-6.845 E.00288
; LINE_WIDTH: 0.151193
G1 X96.834 Y109.068 E.0014
; LINE_WIDTH: 0.185179
G1 X96.676 Y109.051 E.00184
; LINE_WIDTH: 0.220708
G1 X96.504 Y109.032 E.00251
; LINE_WIDTH: 0.261549
G1 X96.386 Y109.01 E.00215
; LINE_WIDTH: 0.304326
G1 F13771.709
G1 X96.267 Y108.989 E.00257
; LINE_WIDTH: 0.347103
G1 F11835.003
G1 X96.148 Y108.967 E.00299
; LINE_WIDTH: 0.38988
G1 F10375.853
G1 X96.03 Y108.946 E.00341
; LINE_WIDTH: 0.426413
G1 F9387.412
G3 X95.796 Y108.887 I.705 J-3.302 E.00755
M204 S10000
G1 X94.732 Y107.66 F42000
; LINE_WIDTH: 0.106641
G1 F15000
M204 S6000
G1 X94.649 Y107.564 E.00066
G3 X94.615 Y107.473 I.093 J-.086 E.00052
M204 S10000
G1 X94.448 Y106.744 F42000
; LINE_WIDTH: 0.497414
G1 F7920.894
M204 S6000
G1 X94.419 Y106.476 E.00998
; LINE_WIDTH: 0.465003
G1 F8529.14
G1 X94.391 Y106.208 E.00927
; LINE_WIDTH: 0.429914
G1 F9302.468
G3 X94.389 Y105.321 I8.939 J-.464 E.028
; LINE_WIDTH: 0.463246
G1 F8564.783
G3 X94.419 Y105.024 I4.169 J.283 E.01023
; LINE_WIDTH: 0.497444
G1 F7920.382
G1 X94.448 Y104.756 E.00999
M204 S10000
G1 X94.615 Y104.027 F42000
; LINE_WIDTH: 0.106646
G1 F15000
M204 S6000
G3 X94.649 Y103.936 I.126 J-.005 E.00052
G1 X94.732 Y103.84 E.00066
M204 S10000
G1 X95.796 Y102.613 F42000
; LINE_WIDTH: 0.426463
G1 F9386.183
M204 S6000
G3 X96.03 Y102.554 I.95 J3.294 E.00755
; LINE_WIDTH: 0.389938
G1 F10374.106
G1 X96.148 Y102.533 E.00341
; LINE_WIDTH: 0.347134
G1 F11833.791
G1 X96.267 Y102.511 E.00299
; LINE_WIDTH: 0.30433
G1 F13771.505
G1 X96.386 Y102.49 E.00257
; LINE_WIDTH: 0.261525
G1 F15000
G1 X96.504 Y102.468 E.00215
; LINE_WIDTH: 0.220674
G1 X96.676 Y102.449 E.00251
; LINE_WIDTH: 0.185143
G1 X96.834 Y102.432 E.00184
; LINE_WIDTH: 0.151159
G1 X96.992 Y102.415 E.0014
; LINE_WIDTH: 0.116351
G3 X97.473 Y102.398 I.477 J6.538 E.00288
G1 X97.951 Y102.415 E.00286
; LINE_WIDTH: 0.150491
G1 X98.116 Y102.432 E.00145
; LINE_WIDTH: 0.185169
G1 X98.274 Y102.449 E.00184
; LINE_WIDTH: 0.219161
G1 X98.432 Y102.466 E.00228
; LINE_WIDTH: 0.259099
G1 X98.564 Y102.49 E.00237
; LINE_WIDTH: 0.30432
G1 F13772.036
G1 X98.683 Y102.511 E.00257
; LINE_WIDTH: 0.347092
G1 F11835.404
G1 X98.801 Y102.533 E.00298
; LINE_WIDTH: 0.389865
G1 F10376.285
G1 X98.92 Y102.554 E.0034
; LINE_WIDTH: 0.426426
G1 F9387.085
G3 X99.154 Y102.613 I-.721 J3.371 E.00756
M204 S10000
G1 X99.82 Y102.777 F42000
; LINE_WIDTH: 0.134116
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.00128
; LINE_WIDTH: 0.108304
G1 X100.065 Y103.04 E.001
; WIPE_START
G1 X99.942 Y102.899 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X106.902 Y103.024 Z2 F42000
G1 Z1.6
G1 E.8 F1800
; LINE_WIDTH: 0.118842
G1 F15000
M204 S6000
G1 X107.133 Y102.777 E.0021
M204 S10000
G1 X107.798 Y102.612 F42000
; LINE_WIDTH: 0.421387
G1 F9512.073
M204 S6000
G3 X108.05 Y102.55 I1.018 J3.566 E.00801
; LINE_WIDTH: 0.381437
G1 F10634.646
G1 X108.169 Y102.529 E.00332
; LINE_WIDTH: 0.339389
G1 F12142.943
G1 X108.288 Y102.507 E.00291
; LINE_WIDTH: 0.297341
G1 F14149.786
G1 X108.406 Y102.486 E.0025
; LINE_WIDTH: 0.255293
G1 F15000
G1 X108.525 Y102.465 E.00208
; LINE_WIDTH: 0.232377
G1 X108.538 Y102.464 E.00021
; LINE_WIDTH: 0.205934
G1 X108.773 Y102.439 E.00313
; LINE_WIDTH: 0.156881
G1 X109.008 Y102.414 E.00219
; LINE_WIDTH: 0.116864
G3 X109.499 Y102.398 I.479 J7.041 E.00296
G1 X109.971 Y102.416 E.00285
; LINE_WIDTH: 0.153904
G1 X110.136 Y102.434 E.0015
; LINE_WIDTH: 0.189571
G1 X110.294 Y102.452 E.0019
; LINE_WIDTH: 0.224512
G1 X110.452 Y102.469 E.00235
; LINE_WIDTH: 0.265192
G1 X110.584 Y102.493 E.00242
; LINE_WIDTH: 0.31083
G1 F13437.354
G1 X110.701 Y102.514 E.0026
; LINE_WIDTH: 0.353904
G1 F11576.189
G1 X110.819 Y102.536 E.00302
; LINE_WIDTH: 0.396977
G1 F10167.872
G1 X110.936 Y102.558 E.00344
; LINE_WIDTH: 0.430472
G1 F9289.092
G3 X111.157 Y102.613 I-.71 J3.296 E.00719
; CHANGE_LAYER
; Z_HEIGHT: 1.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9289.092
G1 X110.936 Y102.558 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 9/79
; update layer progress
M73 L9
M991 S0 P8 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z2 I-.465 J-1.125 P1  F42000
G1 X99.784 Y107.166 Z2
G1 Z1.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.756 Y107.216 E.00189
G3 X95.558 Y107.659 I-2.277 J-1.464 E.16058
G3 X97.288 Y103.052 I1.906 J-1.913 E.20534
G3 X99.942 Y106.876 I.192 J2.7 E.18589
G1 X99.812 Y107.113 E.00895
M204 S10000
G1 X99.426 Y106.971 F42000
G1 F8843.478
M204 S6000
G1 X99.413 Y106.995 E.00093
G3 X95.846 Y107.371 I-1.934 J-1.244 E.13644
G3 X97.317 Y103.458 I1.619 J-1.624 E.17444
G3 X99.57 Y106.707 I.162 J2.294 E.15789
G1 X99.455 Y106.918 E.00799
M204 S250
G1 X99.085 Y106.785 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.345 Y103.849 I-1.602 J-1.034 E.23827
G3 X98.508 Y104.143 I.127 J1.946 E.03748
G3 X99.117 Y106.734 I-1.025 J1.608 E.09052
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.12636
G1 X98.726 Y107.194 E-.10358
G1 X98.508 Y107.357 E-.10362
G1 X98.269 Y107.488 E-.10356
G1 X98.013 Y107.583 E-.10358
G1 X97.747 Y107.641 E-.10358
G1 X97.475 Y107.661 E-.1036
G1 X97.443 Y107.658 E-.01213
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X95.165 Y103.084 E.01901
G1 X94.798 Y103.45 E.01718
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.605 Y102.683 E.00385
; WIPE_START
G1 X95.165 Y103.084 E-.22605
G1 X94.798 Y103.45 E-.19686
G1 X94.798 Y102.573 E-.33323
G1 X94.808 Y102.573 E-.00386
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01718
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07721
G1 X94.798 Y108.927 E-.29241
G1 X94.798 Y108.05 E-.33322
G1 X94.905 Y108.156 E-.05715
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z2.2 F42000
G1 X106.693 Y108.52 Z2.2
G1 Z1.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21186
G1 X100.786 Y107.878 E.02659
G1 X101.055 Y107.385 E.01862
G2 X100.621 Y103.402 I-3.56 J-1.627 E.13954
G1 X100.306 Y102.98 E.01746
G1 X106.648 Y102.98 E.2104
G1 X106.182 Y103.594 E.02556
G2 X106.651 Y108.477 I3.314 J2.146 E.17556
; WIPE_START
G1 X104.651 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.622 Y108.76 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.567 Y108.927 E.00584
G1 X99.382 Y108.927 E.27149
G1 X99.327 Y108.76 E.00584
G1 X99.579 Y108.57 E.01047
G2 X100.443 Y107.657 I-2.269 J-3.01 E.04189
G1 X100.561 Y107.441 E.00816
G2 X99.785 Y103.084 I-3.108 J-1.695 E.1586
G1 X99.327 Y102.74 E.019
G1 X99.382 Y102.573 E.00584
G1 X107.572 Y102.573 E.27167
G1 X107.627 Y102.742 E.00588
G2 X107.352 Y108.557 I1.865 J3.002 E.2269
G1 X107.574 Y108.724 E.00922
; WIPE_START
G1 X107.567 Y108.927 E-.07722
G1 X105.77 Y108.927 E-.68278
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.641 Y108.636 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.329 Y108.75 E.01101
G3 X109.269 Y102.644 I-.848 J-2.998 E.3461
G3 X112.108 Y104.077 I.206 J3.121 E.11068
G3 X110.756 Y108.595 I-2.627 J1.675 E.17743
G1 X110.698 Y108.616 E.00207
M204 S10000
G1 X110.501 Y108.254 F42000
G1 F8843.478
M204 S6000
G1 X110.219 Y108.359 E.01
G3 X109.295 Y103.05 I-.736 J-2.606 E.30073
G3 X111.265 Y103.713 I.17 J2.755 E.07068
G3 X110.589 Y108.225 I-1.782 J2.04 E.17994
G1 X110.558 Y108.235 E.00106
M204 S10000
G1 X110.364 Y107.871 F42000
G1 F8843.478
M204 S6000
G1 X110.269 Y107.906 E.00337
G3 X109.321 Y103.457 I-.794 J-2.157 E.26126
G3 X110.585 Y103.737 I.15 J2.312 E.04352
G3 X110.418 Y107.845 I-1.11 J2.012 E.16883
M204 S250
G1 X110.227 Y107.504 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.136 Y107.544 E.00305
G3 X109.346 Y103.848 I-.653 J-1.793 E.20049
G3 X110.28 Y104.017 I.145 J1.858 E.02948
G3 X110.283 Y107.483 I-.797 J1.734 E.13357
; WIPE_START
M204 S6000
G1 X110.136 Y107.544 E-.06043
G1 X110 Y107.587 E-.05426
G1 X109.734 Y107.643 E-.10331
G1 X109.463 Y107.66 E-.10336
G1 X109.19 Y107.639 E-.10407
G1 X108.924 Y107.579 E-.10333
G1 X108.67 Y107.482 E-.1036
G1 X108.432 Y107.351 E-.1033
G1 X108.381 Y107.312 E-.02434
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.258 Y102.98 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.14089
G1 X116.816 Y105.151 E.07275
G1 X116.816 Y120.02 E.49321
G1 X111.205 Y120.02 E.18612
G1 X111.205 Y109.277 E.35635
G2 X112.427 Y108.352 I-1.916 J-3.801 E.05111
G2 X112.3 Y103.023 I-2.957 J-2.595 E.19428
; WIPE_START
G1 X114.299 Y103.003 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.378 Y102.573 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18322
G1 X116.902 Y102.88 E.01018
G1 X117.223 Y105.122 E.07514
G1 X117.223 Y120.427 E.50768
G1 X110.798 Y120.427 E.21313
G1 X110.798 Y109.013 E.37861
G1 X110.924 Y108.966 E.00445
G2 X111.331 Y102.756 I-1.456 J-3.214 E.25281
G1 X111.363 Y102.631 E.00426
; WIPE_START
G1 X113.363 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.733 Y102.432 Z2.2 F42000
G1 X94.391 Y102.166 Z2.2
G1 Z1.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.63 Y105.093 E.07514
G1 X117.63 Y120.834 E.52214
G1 X110.391 Y120.834 E.24014
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.962 E.07869
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00427
G2 X95.271 Y107.946 I3.01 J-1.444 E.03669
G2 X94.592 Y104.575 I2.208 J-2.198 E.52855
G1 X94.391 Y104.538 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z2.2 F42000
G1 X61.755 Y60.52 Z2.2
G1 Z1.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X118.037 Y105.064 E.07514
G1 X118.037 Y121.114 E.53239
G1 X117.995 Y121.241 E.00444
G1 X109.984 Y121.241 E.26575
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.445 Y105.035 E.07514
G1 X118.445 Y121.179 E.53552
G1 X118.29 Y121.648 E.01638
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.837 Y105.007 E.0696
G1 X118.837 Y121.242 E.49886
G1 X118.573 Y122.04 E.02582
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
M73 P47 R13
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z2.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z2.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z2.2 F4000
            G39.3 S1
            G0 Z2.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z1.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z2.2 F42000
G1 X61.959 Y60.25 Z2.2
G1 Z1.8
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.712 Y106.118 Z2.2 F42000
G1 X110.595 Y109.005 Z2.2
G1 Z1.8
G1 E.8 F1800
; LINE_WIDTH: 0.243618
G1 F15000
M204 S6000
G1 X110.404 Y109.037 E.00316
; LINE_WIDTH: 0.204282
G1 X110.17 Y109.062 E.0031
; LINE_WIDTH: 0.154803
G1 X109.929 Y109.087 E.00221
; LINE_WIDTH: 0.117006
G1 X109.456 Y109.102 E.00286
G3 X108.964 Y109.082 I.026 J-6.876 E.00297
; LINE_WIDTH: 0.156054
G1 X108.808 Y109.065 E.00145
; LINE_WIDTH: 0.190761
G1 X108.652 Y109.048 E.0019
; LINE_WIDTH: 0.227119
G1 X108.481 Y109.028 E.00258
; LINE_WIDTH: 0.268875
G1 X108.362 Y109.006 E.00222
; LINE_WIDTH: 0.312504
G1 F13353.929
M73 P47 R12
G1 X108.244 Y108.985 E.00265
; LINE_WIDTH: 0.356133
G1 F11493.789
G1 X108.125 Y108.963 E.00308
; LINE_WIDTH: 0.399762
G1 F10088.508
G1 X108.006 Y108.941 E.00351
; LINE_WIDTH: 0.428114
G1 F9345.943
G1 X107.983 Y108.936 E.00075
G1 X107.872 Y108.654 E.00951
; WIPE_START
G1 X107.983 Y108.936 E-.70446
G1 X108.006 Y108.941 E-.05554
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.503 Y107.331 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X105.95 Y108.172 I4.219 J-1.704 E.03162
G1 X105.277 Y108.172 E.02233
G2 X104.94 Y107.296 I-1.236 J-.027 E.03191
G3 X104.053 Y106.248 I1.03 J-1.77 E.04644
G3 X105.007 Y104.676 I1.935 J.098 E.06356
G2 X105.066 Y103.329 I-.732 J-.707 E.04889
G1 X103.174 Y103.329 E.06278
G3 X102.843 Y104.151 I-1.169 J.008 E.03017
G2 X101.957 Y105.2 I1.03 J1.77 E.04644
G2 X102.91 Y106.772 I1.935 J-.098 E.06356
G3 X102.94 Y108.172 I-.776 J.717 E.05075
G1 X101.312 Y108.172 E.05401
; WIPE_START
G1 X102.94 Y108.172 E-.61876
G1 X103.122 Y107.847 E-.14124
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y108.46 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108287
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.001
; LINE_WIDTH: 0.134094
G1 X99.82 Y108.723 E.00128
M204 S10000
G1 X99.154 Y108.887 F42000
; LINE_WIDTH: 0.426427
G1 F9387.051
M204 S6000
G3 X98.92 Y108.946 I-.942 J-3.256 E.00755
; LINE_WIDTH: 0.389895
G1 F10375.395
G1 X98.802 Y108.967 E.00341
; LINE_WIDTH: 0.347125
G1 F11834.156
G1 X98.683 Y108.989 E.00299
; LINE_WIDTH: 0.304354
G1 F13770.225
G1 X98.565 Y109.01 E.00257
; LINE_WIDTH: 0.259135
G1 F15000
G1 X98.432 Y109.034 E.00237
; LINE_WIDTH: 0.219181
G1 X98.274 Y109.051 E.00228
; LINE_WIDTH: 0.185183
G1 X98.116 Y109.068 E.00184
; LINE_WIDTH: 0.1505
G1 X97.951 Y109.085 E.00145
; LINE_WIDTH: 0.116375
G1 X97.473 Y109.102 E.00286
G3 X96.992 Y109.085 I-.004 J-6.552 E.00288
; LINE_WIDTH: 0.1512
G1 X96.834 Y109.068 E.0014
; LINE_WIDTH: 0.185198
G1 X96.676 Y109.051 E.00184
; LINE_WIDTH: 0.220742
G1 X96.504 Y109.032 E.00251
; LINE_WIDTH: 0.261588
G1 X96.385 Y109.01 E.00215
; LINE_WIDTH: 0.304363
G1 F13769.746
G1 X96.267 Y108.989 E.00257
; LINE_WIDTH: 0.347138
G1 F11833.623
G1 X96.148 Y108.967 E.00299
; LINE_WIDTH: 0.389913
G1 F10374.848
G1 X96.03 Y108.946 E.00341
; LINE_WIDTH: 0.426444
G1 F9386.643
G3 X95.796 Y108.887 I.722 J-3.378 E.00755
M204 S10000
G1 X94.732 Y107.661 F42000
; LINE_WIDTH: 0.106653
G1 F15000
M204 S6000
G1 X94.649 Y107.564 E.00066
G3 X94.615 Y107.473 I.093 J-.086 E.00052
M204 S10000
G1 X94.448 Y106.744 F42000
; LINE_WIDTH: 0.497413
G1 F7920.912
M204 S6000
G1 X94.419 Y106.476 E.00999
; LINE_WIDTH: 0.465
G1 F8529.204
G1 X94.391 Y106.208 E.00927
; LINE_WIDTH: 0.429914
G1 F9302.468
G3 X94.389 Y105.321 I8.941 J-.464 E.028
; LINE_WIDTH: 0.46323
G1 F8565.105
G3 X94.419 Y105.024 I4.168 J.283 E.01023
; LINE_WIDTH: 0.497435
G1 F7920.54
G1 X94.448 Y104.756 E.00999
M204 S10000
G1 X94.615 Y104.027 F42000
; LINE_WIDTH: 0.106645
G1 F15000
M204 S6000
G3 X94.649 Y103.936 I.127 J-.005 E.00052
G1 X94.732 Y103.84 E.00066
M204 S10000
G1 X95.796 Y102.613 F42000
; LINE_WIDTH: 0.426478
G1 F9385.806
M204 S6000
G3 X96.03 Y102.554 I.945 J3.267 E.00754
; LINE_WIDTH: 0.389976
G1 F10372.99
G1 X96.148 Y102.533 E.00341
; LINE_WIDTH: 0.347166
G1 F11832.545
G1 X96.267 Y102.511 E.00299
; LINE_WIDTH: 0.304356
G1 F13770.099
G1 X96.385 Y102.49 E.00257
; LINE_WIDTH: 0.261547
G1 F15000
G1 X96.504 Y102.468 E.00215
; LINE_WIDTH: 0.220675
G1 X96.676 Y102.449 E.00251
; LINE_WIDTH: 0.185143
G1 X96.834 Y102.432 E.00184
; LINE_WIDTH: 0.151159
G1 X96.992 Y102.415 E.0014
; LINE_WIDTH: 0.116351
G3 X97.473 Y102.398 I.477 J6.538 E.00288
G1 X97.951 Y102.415 E.00286
; LINE_WIDTH: 0.150487
G1 X98.116 Y102.432 E.00145
; LINE_WIDTH: 0.185159
G1 X98.274 Y102.449 E.00184
; LINE_WIDTH: 0.219145
G1 X98.432 Y102.466 E.00228
; LINE_WIDTH: 0.259086
G1 X98.564 Y102.49 E.00237
; LINE_WIDTH: 0.304314
G1 F13772.323
G1 X98.683 Y102.511 E.00257
; LINE_WIDTH: 0.347097
G1 F11835.241
G1 X98.802 Y102.533 E.00299
; LINE_WIDTH: 0.389879
G1 F10375.871
G1 X98.92 Y102.554 E.00341
; LINE_WIDTH: 0.426433
G1 F9386.923
G3 X99.154 Y102.613 I-.709 J3.319 E.00755
M204 S10000
G1 X99.82 Y102.777 F42000
; LINE_WIDTH: 0.134094
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.00128
; LINE_WIDTH: 0.108299
G1 X100.065 Y103.04 E.001
; WIPE_START
G1 X99.942 Y102.899 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X106.904 Y103.023 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
; LINE_WIDTH: 0.118625
G1 F15000
M204 S6000
G1 X107.134 Y102.777 E.00208
M204 S10000
G1 X107.799 Y102.612 F42000
; LINE_WIDTH: 0.420785
G1 F9527.234
M204 S6000
G3 X108.053 Y102.549 I1.015 J3.549 E.00808
; LINE_WIDTH: 0.380319
G1 F10669.872
G1 X108.172 Y102.528 E.00331
; LINE_WIDTH: 0.338356
G1 F12185.388
G1 X108.29 Y102.507 E.0029
; LINE_WIDTH: 0.296393
G1 F14202.694
G1 X108.409 Y102.486 E.00249
; LINE_WIDTH: 0.254431
G1 F15000
G1 X108.528 Y102.465 E.00208
; LINE_WIDTH: 0.231562
G1 X108.541 Y102.463 E.00021
; LINE_WIDTH: 0.205299
G1 X108.775 Y102.439 E.00312
; LINE_WIDTH: 0.156535
G1 X109.01 Y102.414 E.00218
; LINE_WIDTH: 0.116906
G3 X109.501 Y102.398 I.474 J6.924 E.00296
G1 X109.974 Y102.417 E.00286
; LINE_WIDTH: 0.154393
G1 X110.139 Y102.435 E.0015
; LINE_WIDTH: 0.19018
G1 X110.297 Y102.452 E.00191
; LINE_WIDTH: 0.225233
G1 X110.455 Y102.47 E.00236
; LINE_WIDTH: 0.265997
G1 X110.586 Y102.493 E.00243
; LINE_WIDTH: 0.311724
G1 F13392.683
G1 X110.704 Y102.515 E.00261
; LINE_WIDTH: 0.354873
G1 F11540.218
G1 X110.821 Y102.537 E.00303
; LINE_WIDTH: 0.398022
G1 F10137.947
G1 X110.938 Y102.558 E.00345
; LINE_WIDTH: 0.431266
G1 F9270.097
G3 X111.157 Y102.613 I-.729 J3.378 E.00715
; WIPE_START
G1 X110.938 Y102.558 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.74 Y106.018 Z2.2 F42000
G1 Z1.8
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X113.538 Y104.415 I-3.377 J-.388 E.05412
G2 X113.452 Y103.329 I-.812 J-.483 E.03853
G1 X115.753 Y103.329 E.07632
G3 X115.423 Y104.151 I-1.169 J.008 E.03017
G2 X114.536 Y105.2 I1.03 J1.77 E.04644
G2 X114.894 Y106.248 I1.458 J.087 E.03769
G3 X115.781 Y107.296 I-1.03 J1.77 E.04644
G3 X115.423 Y108.344 I-1.458 J.087 E.03769
G2 X114.536 Y109.393 I1.03 J1.77 E.04644
G2 X114.894 Y110.441 I1.458 J.087 E.03769
G3 X115.781 Y111.489 I-1.03 J1.77 E.04644
G3 X115.423 Y112.538 I-1.458 J.087 E.03769
G2 X114.536 Y113.586 I1.03 J1.77 E.04644
G2 X114.894 Y114.634 I1.458 J.087 E.03769
G3 X115.781 Y115.682 I-1.03 J1.77 E.04644
G3 X115.423 Y116.731 I-1.458 J.087 E.03769
G2 X114.536 Y117.779 I1.03 J1.77 E.04644
G2 X115.489 Y119.351 I1.935 J-.098 E.06356
G1 X115.667 Y119.672 E.01215
G1 X113.094 Y119.672 E.08535
G3 X112.439 Y118.827 I.859 J-1.343 E.03615
G3 X112.797 Y117.779 I1.458 J-.087 E.03769
G2 X113.684 Y116.731 I-1.03 J-1.77 E.04644
G2 X113.326 Y115.682 I-1.458 J-.087 E.03769
G3 X112.439 Y114.634 I1.03 J-1.77 E.04644
G3 X112.797 Y113.586 I1.458 J-.087 E.03769
G2 X113.684 Y112.538 I-1.03 J-1.77 E.04644
G2 X113.326 Y111.489 I-1.458 J-.087 E.03769
G3 X112.439 Y110.441 I1.03 J-1.77 E.04644
G3 X113.393 Y108.869 I1.935 J.098 E.06356
G2 X113.406 Y107.438 I-.802 J-.722 E.05186
G3 X111.554 Y109.485 I-3.798 J-1.575 E.09338
G3 X111.554 Y111.766 I-17.871 J1.141 E.07572
G1 X111.554 Y115.621 E.12787
G3 X111.554 Y115.959 I-.232 J.169 E.012
G1 X111.554 Y117.588 E.05401
; CHANGE_LAYER
; Z_HEIGHT: 2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8843.478
G1 X111.554 Y115.959 E-.61876
G1 X111.554 Y115.621 E-.12853
G1 X111.554 Y115.588 E-.01271
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 10/79
; update layer progress
M73 L10
M991 S0 P9 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z2.2 I.7 J-.995 P1  F42000
G1 X99.722 Y107.262 Z2.2
G1 Z2
G1 E.8 F1800
; FEATURE: Inner wall
G1 F8843.478
M204 S6000
G1 X99.636 Y107.394 E.00522
G3 X97.303 Y103.051 I-2.154 J-1.641 E.35887
G3 X99.524 Y103.974 I.168 J2.731 E.08264
M73 P48 R12
G3 X99.761 Y107.216 I-2.042 J1.778 E.11564
M204 S10000
G1 X99.396 Y107.018 F42000
G1 F8843.478
M204 S6000
G1 X99.219 Y107.261 E.00999
G3 X97.332 Y103.457 I-1.736 J-1.509 E.30001
G3 X98.984 Y104.009 I.158 J2.274 E.05929
G3 X99.433 Y106.971 I-1.501 J1.743 E.10823
M204 S250
G1 X99.085 Y106.785 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.36 Y103.848 I-1.603 J-1.034 E.23882
G3 X98.508 Y104.143 I.112 J1.948 E.03702
G3 X99.117 Y106.734 I-1.025 J1.608 E.09053
; WIPE_START
M204 S6000
G1 X98.988 Y106.908 E-.08238
G1 X98.726 Y107.194 E-.14727
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10357
G1 X97.747 Y107.641 E-.10358
G1 X97.475 Y107.661 E-.10359
G1 X97.442 Y107.658 E-.01244
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z2.4 F42000
G1 Z2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X95.165 Y103.084 E.01901
G1 X94.798 Y103.45 E.01719
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.165 Y103.084 E-.22602
G1 X94.798 Y103.45 E-.19687
G1 X94.798 Y102.573 E-.33322
G1 X94.809 Y102.573 E-.0039
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z2.4 F42000
G1 Z2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01719
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29242
G1 X94.798 Y108.05 E-.33324
G1 X94.905 Y108.156 E-.05713
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z2.4 F42000
G1 X106.692 Y108.52 Z2.4
G1 Z2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21186
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.311 J-2.128 E.14915
G1 X100.306 Y102.98 E.02659
G1 X106.649 Y102.98 E.21041
G1 X106.184 Y103.592 E.0255
G2 X106.651 Y108.477 I3.313 J2.148 E.17563
; WIPE_START
G1 X104.651 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.622 Y108.76 Z2.4 F42000
G1 Z2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.566 Y108.927 E.00584
G1 X99.382 Y108.927 E.27149
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18578
G2 X99.327 Y102.74 I-3.356 J2.283 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.572 Y102.573 E.27167
G1 X107.627 Y102.742 E.00588
G2 X107.362 Y108.565 I1.865 J3.002 E.22734
G1 X107.574 Y108.724 E.00878
; WIPE_START
G1 X107.566 Y108.927 E-.07722
G1 X105.77 Y108.927 E-.68278
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.631 Y108.64 Z2.4 F42000
G1 Z2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.328 Y108.751 E.01073
G3 X109.255 Y102.645 I-.846 J-2.998 E.34562
G3 X112.109 Y104.079 I.22 J3.119 E.11118
G3 X110.755 Y108.596 I-2.628 J1.674 E.17743
G1 X110.688 Y108.62 E.00235
M204 S10000
G1 X110.497 Y108.256 F42000
G1 F8843.478
M204 S6000
G1 X110.424 Y108.291 E.00269
G3 X109.281 Y103.051 I-.941 J-2.539 E.3074
G3 X111.266 Y103.714 I.183 J2.754 E.07119
G3 X110.587 Y108.224 I-1.784 J2.037 E.17988
G1 X110.554 Y108.236 E.00115
M204 S10000
G1 X110.355 Y107.875 F42000
G1 F8843.478
M204 S6000
G1 X110.282 Y107.901 E.00259
G3 X109.308 Y103.458 I-.807 J-2.152 E.26128
G3 X110.573 Y103.731 I.163 J2.313 E.04352
G3 X110.416 Y107.846 I-1.098 J2.019 E.16938
G1 X110.409 Y107.849 E.00023
M204 S250
G1 X110.215 Y107.501 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.149 Y107.539 E.00233
G3 X109.333 Y103.849 I-.667 J-1.788 E.20053
G3 X110.281 Y104.018 I.157 J1.86 E.02994
G3 X110.497 Y107.367 I-.798 J1.733 E.12603
G1 X110.269 Y107.476 E.00776
; WIPE_START
M204 S6000
G1 X110.149 Y107.539 E-.05154
G1 X109.999 Y107.587 E-.06008
G1 X109.733 Y107.643 E-.10334
G1 X109.461 Y107.66 E-.10329
G1 X109.188 Y107.639 E-.10411
G1 X108.923 Y107.579 E-.10336
G1 X108.668 Y107.482 E-.10357
G1 X108.431 Y107.35 E-.10329
G1 X108.373 Y107.306 E-.02742
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.258 Y102.98 Z2.4 F42000
G1 Z2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.14089
G1 X116.854 Y105.415 E.08159
G1 X116.854 Y120.02 E.48446
G1 X111.205 Y120.02 E.18738
G1 X111.205 Y109.277 E.35636
G2 X112.426 Y108.354 I-1.915 J-3.801 E.05103
G2 X112.3 Y103.023 I-2.955 J-2.597 E.19436
; WIPE_START
G1 X114.3 Y103.003 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.378 Y102.573 Z2.4 F42000
G1 Z2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18322
G1 X116.902 Y102.88 E.01018
G1 X117.261 Y105.386 E.08398
G1 X117.261 Y120.427 E.49892
G1 X110.798 Y120.427 E.21439
G1 X110.798 Y109.013 E.37861
G1 X110.922 Y108.967 E.00439
G2 X111.33 Y102.756 I-1.454 J-3.215 E.25289
G1 X111.363 Y102.631 E.00426
; WIPE_START
G1 X113.363 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.733 Y102.432 Z2.4 F42000
G1 X94.391 Y102.166 Z2.4
G1 Z2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.668 Y105.357 E.08398
G1 X117.668 Y120.834 E.51339
G1 X110.391 Y120.834 E.24139
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.961 E.0787
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00428
G2 X94.637 Y104.454 I2.833 J-1.296 E.56069
G1 X94.592 Y104.575 E.00428
G1 X94.391 Y104.539 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z2.4 F42000
G1 X61.755 Y60.52 Z2.4
G1 Z2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X118.075 Y105.328 E.08398
G1 X118.075 Y120.999 E.51984
G1 X117.995 Y121.241 E.00845
G1 X109.984 Y121.241 E.26575
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.482 Y105.299 E.08398
G1 X118.482 Y121.065 E.52297
G1 X118.29 Y121.648 E.02038
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.874 Y105.271 E.07779
G1 X118.874 Y121.128 E.48723
G1 X118.573 Y122.04 E.02953
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z2.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z2.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z2.4 F4000
            G39.3 S1
            G0 Z2.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z2.4 F42000
G1 X61.959 Y60.25 Z2.4
G1 Z2
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z2.4 F42000
G1 Z2
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.077 Y105.104 Z2.4 F42000
G1 Z2
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
M73 P49 R12
G1 F8843.478
M204 S6000
G1 X115.876 Y103.706 E.04686
G1 X115.66 Y103.706 E.00715
G1 X115.516 Y104.151 E.01554
G2 X114.688 Y105.2 I4.932 J4.747 E.04438
G2 X115.256 Y106.772 I1.517 J.341 E.05855
G1 X115.628 Y107.296 E.02133
G3 X115.061 Y108.869 I-1.517 J.341 E.05855
G1 X114.688 Y109.393 E.02133
G2 X115.256 Y110.965 I1.517 J.341 E.05855
G1 X115.628 Y111.489 E.02133
G3 X115.061 Y113.062 I-1.517 J.341 E.05855
G1 X114.688 Y113.586 E.02133
G2 X115.256 Y115.158 I1.517 J.341 E.05855
G1 X115.628 Y115.682 E.02133
G3 X115.061 Y117.255 I-1.517 J.341 E.05855
G1 X114.688 Y117.779 E.02133
G2 X115.256 Y119.351 I1.517 J.341 E.05855
G1 X115.483 Y119.671 E.01303
G1 X113.242 Y119.671 E.07433
G3 X112.592 Y118.827 I3.981 J-3.741 E.03542
G3 X113.159 Y117.255 I1.517 J-.341 E.05855
G1 X113.532 Y116.731 E.02133
G2 X112.964 Y115.158 I-1.517 J-.341 E.05855
G1 X112.592 Y114.634 E.02133
G3 X113.159 Y113.062 I1.517 J-.341 E.05855
G1 X113.532 Y112.538 E.02133
G2 X112.964 Y110.965 I-1.517 J-.341 E.05855
G1 X112.592 Y110.441 E.02133
G3 X113.159 Y108.869 I1.517 J-.341 E.05855
G1 X113.532 Y108.344 E.02133
G3 X113.939 Y107.098 I4.13 J.661 E.04367
G1 X113.974 Y106.943 E.00529
G2 X114.088 Y106.412 I-1.786 J-.659 E.01807
; WIPE_START
G1 X113.974 Y106.943 E-.20628
G1 X113.939 Y107.098 E-.06056
G1 X113.575 Y107.947 E-.35105
G1 X113.534 Y108.319 E-.14211
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.595 Y109.005 Z2.4 F42000
G1 Z2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.243325
G1 F15000
M204 S6000
G1 X110.402 Y109.038 E.00319
; LINE_WIDTH: 0.203717
G1 X110.167 Y109.062 E.00309
; LINE_WIDTH: 0.154352
G1 X109.926 Y109.087 E.0022
; LINE_WIDTH: 0.117005
G1 X109.454 Y109.102 E.00285
G3 X108.962 Y109.082 I.031 J-6.976 E.00297
; LINE_WIDTH: 0.156384
G1 X108.806 Y109.065 E.00146
; LINE_WIDTH: 0.19127
G1 X108.649 Y109.047 E.00191
; LINE_WIDTH: 0.227818
G1 X108.478 Y109.028 E.00259
; LINE_WIDTH: 0.26974
G1 X108.359 Y109.006 E.00223
; LINE_WIDTH: 0.31346
G1 F13306.72
G1 X108.241 Y108.984 E.00266
; LINE_WIDTH: 0.35718
G1 F11455.484
G1 X108.122 Y108.962 E.00309
; LINE_WIDTH: 0.4009
G1 F10056.428
G1 X108.004 Y108.94 E.00352
; LINE_WIDTH: 0.426145
G1 F9393.972
G1 X107.983 Y108.936 E.00067
G1 X107.871 Y108.656 E.00941
; WIPE_START
G1 X107.983 Y108.936 E-.70986
G1 X108.004 Y108.94 E-.05014
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X106.906 Y103.021 Z2.4 F42000
G1 Z2
G1 E.8 F1800
; LINE_WIDTH: 0.11842
G1 F15000
M204 S6000
G1 X107.134 Y102.777 E.00206
M204 S10000
G1 X107.799 Y102.612 F42000
; LINE_WIDTH: 0.420146
G1 F9543.361
M204 S6000
G3 X108.056 Y102.548 I1.02 J3.571 E.00815
; LINE_WIDTH: 0.379193
G1 F10705.588
G1 X108.175 Y102.527 E.0033
; LINE_WIDTH: 0.337339
G1 F12227.476
G1 X108.293 Y102.507 E.00289
; LINE_WIDTH: 0.295485
G1 F14253.769
G1 X108.412 Y102.486 E.00248
; LINE_WIDTH: 0.253631
G1 F15000
G1 X108.53 Y102.465 E.00207
; LINE_WIDTH: 0.230828
G1 X108.544 Y102.463 E.00021
; LINE_WIDTH: 0.204689
G1 X108.778 Y102.439 E.0031
; LINE_WIDTH: 0.156185
G1 X109.012 Y102.414 E.00217
; LINE_WIDTH: 0.116939
G3 X109.503 Y102.398 I.478 J7.118 E.00296
G1 X109.977 Y102.417 E.00286
; LINE_WIDTH: 0.154851
G1 X110.141 Y102.435 E.00151
; LINE_WIDTH: 0.190807
G1 X110.3 Y102.453 E.00192
; LINE_WIDTH: 0.226025
G1 X110.458 Y102.47 E.00237
; LINE_WIDTH: 0.266874
G1 X110.589 Y102.494 E.00244
; LINE_WIDTH: 0.312612
G1 F13348.589
G1 X110.706 Y102.515 E.00261
; LINE_WIDTH: 0.355753
G1 F11507.759
G1 X110.823 Y102.537 E.00303
; LINE_WIDTH: 0.398894
G1 F10113.118
G1 X110.94 Y102.559 E.00345
; LINE_WIDTH: 0.431669
G1 F9260.484
G3 X111.157 Y102.613 I-.647 J3.012 E.00709
; WIPE_START
G1 X110.94 Y102.559 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X104.273 Y103.706 Z2.4 F42000
G1 Z2
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X105.291 Y103.706 E.03376
G3 X104.318 Y105.2 I-3.578 J-1.267 E.0597
G2 X104.578 Y106.772 I1.166 J.615 E.05677
G1 X105.034 Y107.296 E.02304
G1 X105.195 Y107.794 E.01736
G1 X103.104 Y107.794 E.06936
G1 X103.049 Y107.296 E.01662
G2 X102.221 Y106.248 I-5.76 J3.699 E.04438
G3 X102.109 Y105.2 I3.327 J-.885 E.03511
G3 X102.937 Y104.151 I5.76 J3.699 E.04438
G1 X103.081 Y103.706 E.01554
G1 X101.659 Y103.706 E.0472
G3 X101.746 Y103.891 I-.6 J.397 E.00682
; WIPE_START
G1 X101.659 Y103.706 E-.0779
G1 X103.081 Y103.706 E-.54066
G1 X102.967 Y104.06 E-.14143
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z2.4 F42000
G1 Z2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108313
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134126
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.426423
G1 F9387.168
M204 S6000
G2 X98.92 Y102.554 I-.941 J3.25 E.00755
; LINE_WIDTH: 0.389878
G1 F10375.903
G1 X98.802 Y102.533 E.00341
; LINE_WIDTH: 0.347107
G1 F11834.827
G1 X98.683 Y102.511 E.00299
; LINE_WIDTH: 0.304337
G1 F13771.144
G1 X98.565 Y102.49 E.00257
; LINE_WIDTH: 0.259119
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219178
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185179
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150494
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.116351
G1 X97.473 Y102.398 E.00286
G2 X96.992 Y102.415 I-.003 J6.555 E.00288
; LINE_WIDTH: 0.151159
G1 X96.834 Y102.432 E.0014
; LINE_WIDTH: 0.185143
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.220674
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.26152
G1 X96.386 Y102.49 E.00215
; LINE_WIDTH: 0.304315
G1 F13772.295
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347109
G1 F11834.763
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.389903
G1 F10375.152
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426458
G1 F9386.307
G2 X95.796 Y102.613 I.715 J3.344 E.00755
M204 S10000
G1 X94.733 Y103.839 F42000
; LINE_WIDTH: 0.10666
G1 F15000
M204 S6000
G1 X94.649 Y103.936 E.00067
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497441
G1 F7920.428
M204 S6000
G1 X94.419 Y105.024 E.00999
; LINE_WIDTH: 0.463245
G1 F8564.801
G2 X94.389 Y105.321 I4.137 J.58 E.01023
; LINE_WIDTH: 0.429914
G1 F9302.473
G2 X94.391 Y106.208 I8.941 J.423 E.028
; LINE_WIDTH: 0.464995
G1 F8529.305
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.497398
G1 F7921.174
G1 X94.448 Y106.744 E.00998
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.106626
G1 F15000
M204 S6000
G2 X94.649 Y107.563 I.126 J.005 E.00051
G1 X94.732 Y107.66 E.00066
M204 S10000
G1 X95.796 Y108.887 F42000
; LINE_WIDTH: 0.426421
G1 F9387.198
M204 S6000
G2 X96.03 Y108.946 I.952 J-3.298 E.00755
; LINE_WIDTH: 0.389874
G1 F10376.011
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.34711
G1 F11834.705
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304346
G1 F13770.623
G1 X96.386 Y109.01 E.00257
; LINE_WIDTH: 0.261582
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.22074
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185198
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.1512
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.11638
G2 X97.473 Y109.102 I.477 J-6.534 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.1505
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185183
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219181
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259135
G1 X98.565 Y109.01 E.00237
; LINE_WIDTH: 0.304347
G1 F13770.618
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.347112
G1 F11834.643
G1 X98.802 Y108.967 E.00299
; LINE_WIDTH: 0.389878
G1 F10375.919
G1 X98.92 Y108.946 E.00341
; LINE_WIDTH: 0.426425
G1 F9387.112
G2 X99.154 Y108.887 I-.724 J-3.383 E.00755
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.13412
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.108301
G1 X100.065 Y108.46 E.001
; WIPE_START
G1 X99.942 Y108.601 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X101.316 Y108.157 Z2.4 F42000
G1 Z2
G1 E.8 F1800
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.38292
G1 F10588.235
M204 S6000
G1 X105.633 Y108.157 E.11962
; LINE_WIDTH: 0.40393
G1 F9972.023
G1 X105.725 Y108.131 E.00281
; LINE_WIDTH: 0.432047
G1 F9251.49
G1 X105.817 Y108.104 E.00303
G1 X105.773 Y107.922 E.00592
; LINE_WIDTH: 0.38292
G1 F10588.235
G3 X105.776 Y103.58 I3.64 J-2.17 E.12633
; LINE_WIDTH: 0.403565
G1 F9982.115
G1 X105.797 Y103.487 E.00278
; LINE_WIDTH: 0.431092
G1 F9274.257
G1 X105.819 Y103.395 E.003
G1 X105.637 Y103.343 E.00599
; LINE_WIDTH: 0.38292
G1 F10588.235
G1 X101.316 Y103.343 E.11971
; LINE_WIDTH: 0.403485
G1 F9984.33
G1 X101.225 Y103.369 E.00278
; LINE_WIDTH: 0.430921
G1 F9278.332
G1 X101.134 Y103.395 E.00299
G1 X101.176 Y103.579 E.00596
; LINE_WIDTH: 0.38292
G1 F10588.235
G3 X101.164 Y107.946 I-3.65 J2.174 E.12709
; LINE_WIDTH: 0.403485
G1 F9984.33
G1 X101.149 Y108.026 E.00237
; LINE_WIDTH: 0.431966
G1 F9253.42
G1 X101.134 Y108.105 E.00256
G1 X101.258 Y108.14 E.00409
; WIPE_START
G1 X101.134 Y108.105 E-.46748
G1 X101.149 Y108.026 E-.29252
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.351 Y112.474 Z2.4 F42000
G1 X111.568 Y115.499 Z2.4
G1 Z2
G1 E.8 F1800
; LINE_WIDTH: 0.383961
G1 F10555.92
M204 S6000
G1 X111.568 Y109.589 E.16424
G1 X111.58 Y109.501 E.00247
G1 X112.257 Y109.027 E.02296
G2 X113.406 Y104.01 I-2.835 J-3.289 E.15311
G1 X113.136 Y103.441 E.01749
; LINE_WIDTH: 0.428418
G1 F9338.576
G1 X113.133 Y103.396 E.00144
G1 X113.316 Y103.343 E.00598
; LINE_WIDTH: 0.383218
G1 F10578.972
G1 X116.052 Y103.343 E.07589
G1 X116.171 Y103.365 E.00335
G1 X116.21 Y103.48 E.00335
G1 X116.491 Y105.441 E.05494
G1 X116.51 Y105.716 E.00765
G1 X116.51 Y109.604 E.10781
G1 X116.497 Y109.729 E.00349
; CHANGE_LAYER
; Z_HEIGHT: 2.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F10578.972
G1 X116.51 Y109.604 E-.04785
G1 X116.51 Y107.73 E-.71215
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 11/79
; update layer progress
M73 L11
M991 S0 P10 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z2.4 I.034 J-1.216 P1  F42000
G1 X99.722 Y107.262 Z2.4
G1 Z2.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.527 Y107.528 E.01095
G3 X97.317 Y103.05 I-2.045 J-1.775 E.35363
G3 X99.524 Y103.974 I.152 J2.733 E.08215
G3 X99.761 Y107.216 I-2.042 J1.778 E.11565
M204 S10000
G1 X99.396 Y107.018 F42000
G1 F8843.478
M204 S6000
G1 X99.219 Y107.261 E.00998
G3 X97.346 Y103.456 I-1.737 J-1.509 E.30052
G3 X98.984 Y104.009 I.143 J2.275 E.05879
G3 X99.433 Y106.971 I-1.501 J1.743 E.10823
M204 S250
G1 X99.085 Y106.785 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.374 Y103.847 I-1.603 J-1.034 E.23929
G3 X98.508 Y104.143 I.095 J1.953 E.03656
G3 X99.117 Y106.734 I-1.026 J1.608 E.09052
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.12636
G1 X98.726 Y107.194 E-.1036
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10357
G1 X97.747 Y107.641 E-.10357
G1 X97.475 Y107.661 E-.1036
G1 X97.443 Y107.658 E-.01212
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X95.394 Y102.912 E.00949
G2 X94.798 Y103.45 I1.576 J2.345 E.02674
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.394 Y102.912 E-.11787
G1 X95.165 Y103.084 E-.10905
G1 X94.798 Y103.45 E-.19693
G1 X94.798 Y102.573 E-.33322
G1 X94.806 Y102.573 E-.00293
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01719
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29242
G1 X94.798 Y108.05 E-.33323
G1 X94.905 Y108.156 E-.05713
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z2.6 F42000
G1 X106.692 Y108.52 Z2.6
G1 Z2.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21185
G1 X100.786 Y107.878 E.02659
G2 X100.639 Y103.426 I-3.338 J-2.118 E.15697
G1 X100.306 Y102.98 E.01845
G1 X106.649 Y102.98 E.21043
G1 X106.185 Y103.59 E.02543
G2 X106.65 Y108.477 I3.313 J2.15 E.17571
; WIPE_START
G1 X104.65 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.622 Y108.76 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.566 Y108.927 E.00584
G1 X99.382 Y108.927 E.27148
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18577
G1 X100.313 Y103.67 E.00718
G2 X99.327 Y102.74 I-3.115 J2.32 E.04519
G1 X99.382 Y102.573 E.00584
G1 X107.572 Y102.573 E.27168
G1 X107.627 Y102.742 E.00588
G2 X107.373 Y108.573 I1.865 J3.003 E.22779
G1 X107.574 Y108.724 E.00833
; WIPE_START
G1 X107.566 Y108.927 E-.07722
G1 X105.77 Y108.927 E-.68278
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.625 Y108.642 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.326 Y108.751 E.01056
G3 X109.242 Y102.646 I-.845 J-2.999 E.34512
G3 X112.11 Y104.08 I.235 J3.116 E.11171
G3 X110.753 Y108.597 I-2.629 J1.672 E.17743
G1 X110.681 Y108.622 E.00252
M204 S10000
G1 X110.485 Y108.26 F42000
G1 F8843.478
M204 S6000
G1 X110.215 Y108.36 E.00955
G3 X109.268 Y103.052 I-.733 J-2.607 E.29975
G3 X111.268 Y103.716 I.197 J2.753 E.07171
G3 X110.585 Y108.226 I-1.785 J2.037 E.1799
G1 X110.542 Y108.241 E.00152
M204 S10000
G1 X110.349 Y107.877 F42000
G1 F8843.478
M204 S6000
G1 X110.294 Y107.897 E.00192
G3 X109.294 Y103.458 I-.819 J-2.147 E.26128
G3 X110.561 Y103.724 I.176 J2.317 E.04352
G3 X110.414 Y107.847 I-1.086 J2.026 E.16989
G1 X110.403 Y107.852 E.0004
M204 S250
G1 X110.21 Y107.505 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.162 Y107.533 E.00171
G3 X109.319 Y103.85 I-.679 J-1.783 E.2005
G3 X110.282 Y104.019 I.17 J1.862 E.0304
G3 X110.495 Y107.367 I-.8 J1.732 E.12599
G1 X110.264 Y107.479 E.0079
; WIPE_START
M204 S6000
G1 X110.162 Y107.533 E-.04389
G1 X109.997 Y107.588 E-.06577
G1 X109.731 Y107.643 E-.10339
G1 X109.46 Y107.66 E-.10326
G1 X109.187 Y107.639 E-.10411
G1 X108.921 Y107.579 E-.10339
G1 X108.667 Y107.481 E-.10357
G1 X108.429 Y107.349 E-.10326
G1 X108.368 Y107.302 E-.02937
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.258 Y102.98 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.14089
G1 X116.892 Y105.679 E.09043
G1 X116.892 Y120.02 E.47571
G1 X111.205 Y120.02 E.18864
G1 X111.205 Y109.277 E.35636
G2 X112.424 Y108.356 I-1.913 J-3.8 E.05096
G2 X112.3 Y103.023 I-2.953 J-2.599 E.19444
; WIPE_START
G1 X114.299 Y103.003 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.378 Y102.573 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18323
G1 X116.902 Y102.88 E.01018
G1 X117.299 Y105.65 E.09282
G1 X117.299 Y120.427 E.49017
G1 X110.798 Y120.427 E.21564
G1 X110.798 Y109.013 E.37861
G1 X110.92 Y108.968 E.00432
G2 X111.33 Y102.756 I-1.451 J-3.215 E.25298
G1 X111.363 Y102.631 E.00426
; WIPE_START
G1 X113.363 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.732 Y102.432 Z2.6 F42000
G1 X94.391 Y102.166 Z2.6
G1 Z2.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.706 Y105.621 E.09282
G1 X117.706 Y120.834 E.50464
G1 X110.391 Y120.834 E.24265
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.961 E.07869
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00428
G2 X94.637 Y104.454 I2.833 J-1.296 E.56072
G1 X94.592 Y104.575 E.00427
G1 X94.391 Y104.538 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z2.6 F42000
G1 X61.755 Y60.52 Z2.6
G1 Z2.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
M73 P50 R12
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X118.113 Y105.592 E.09282
G1 X118.113 Y120.884 E.50729
G1 X117.995 Y121.241 E.01245
G1 X109.984 Y121.241 E.26575
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.52 Y105.563 E.09282
G1 X118.52 Y120.95 E.51042
G1 X118.29 Y121.648 E.02438
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.912 Y105.535 E.08598
G1 X118.912 Y121.013 E.4756
G1 X118.573 Y122.04 E.03323
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z2.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z2.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z2.6 F4000
            G39.3 S1
            G0 Z2.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z2.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z2.6 F42000
G1 X61.959 Y60.25 Z2.6
G1 Z2.2
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.712 Y106.118 Z2.6 F42000
G1 X110.595 Y109.005 Z2.6
G1 Z2.2
G1 E.8 F1800
; LINE_WIDTH: 0.243032
G1 F15000
M204 S6000
G1 X110.4 Y109.038 E.00322
; LINE_WIDTH: 0.203147
G1 X110.165 Y109.062 E.00309
; LINE_WIDTH: 0.153926
G1 X109.923 Y109.087 E.0022
; LINE_WIDTH: 0.117038
G1 X109.452 Y109.102 E.00285
G3 X108.96 Y109.082 I.026 J-6.815 E.00297
; LINE_WIDTH: 0.156812
G1 X108.803 Y109.065 E.00146
; LINE_WIDTH: 0.191834
G1 X108.647 Y109.047 E.00191
; LINE_WIDTH: 0.228531
G1 X108.475 Y109.027 E.00261
; LINE_WIDTH: 0.270589
G1 X108.357 Y109.005 E.00224
; LINE_WIDTH: 0.314407
G1 F13260.32
G1 X108.238 Y108.984 E.00267
; LINE_WIDTH: 0.358225
G1 F11417.538
G1 X108.12 Y108.962 E.0031
; LINE_WIDTH: 0.402043
M73 P51 R12
G1 F10024.443
G1 X108.001 Y108.94 E.00353
; LINE_WIDTH: 0.424078
G1 F9444.911
G1 X107.983 Y108.936 E.00058
G1 X107.871 Y108.657 E.00932
; WIPE_START
G1 X107.983 Y108.936 E-.71558
G1 X108.001 Y108.94 E-.04442
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X106.908 Y103.018 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
; LINE_WIDTH: 0.118136
G1 F15000
M204 S6000
G1 X107.135 Y102.777 E.00203
M204 S10000
G1 X107.799 Y102.612 F42000
; LINE_WIDTH: 0.419525
G1 F9559.108
M204 S6000
G3 X108.059 Y102.548 I1.034 J3.627 E.00822
; LINE_WIDTH: 0.378066
G1 F10741.593
G1 X108.177 Y102.527 E.00329
; LINE_WIDTH: 0.336318
G1 F12270.043
G1 X108.296 Y102.506 E.00288
; LINE_WIDTH: 0.29457
G1 F14305.631
G1 X108.414 Y102.485 E.00247
; LINE_WIDTH: 0.252821
G1 F15000
G1 X108.533 Y102.464 E.00206
; LINE_WIDTH: 0.230077
G1 X108.546 Y102.462 E.00021
; LINE_WIDTH: 0.204079
G1 X108.78 Y102.438 E.00308
; LINE_WIDTH: 0.155796
G1 X109.014 Y102.414 E.00216
; LINE_WIDTH: 0.116941
G3 X109.505 Y102.398 I.463 J6.697 E.00296
G1 X109.979 Y102.417 E.00286
; LINE_WIDTH: 0.155318
G1 X110.144 Y102.435 E.00152
; LINE_WIDTH: 0.191384
G1 X110.302 Y102.453 E.00192
; LINE_WIDTH: 0.226707
G1 X110.46 Y102.47 E.00238
; LINE_WIDTH: 0.267658
G1 X110.592 Y102.494 E.00245
; LINE_WIDTH: 0.313456
G1 F13306.958
G1 X110.709 Y102.516 E.00262
; LINE_WIDTH: 0.356639
G1 F11475.251
G1 X110.825 Y102.537 E.00304
; LINE_WIDTH: 0.399822
G1 F10086.802
G1 X110.942 Y102.559 E.00346
; LINE_WIDTH: 0.432138
G1 F9249.327
G1 X110.968 Y102.565 E.00084
G1 X111.09 Y102.854 E.00995
; WIPE_START
G1 X110.968 Y102.565 E-.70078
G1 X110.942 Y102.559 E-.05922
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.025 Y103.71 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
; FEATURE: Bridge
; LINE_WIDTH: 0.40118
; LAYER_HEIGHT: 0.4
M106 S255
G1 F3000
M204 S6000
G1 X113.661 Y103.35 E.03768
G1 X114.577 Y103.35 E.04717
G1 X113.413 Y104.009 E.06891
G1 X113.569 Y104.439 E.02356
G1 X115.493 Y103.35 E.11386
G1 X116.184 Y103.35 E.0356
G1 X116.201 Y103.468 E.00612
G1 X113.684 Y104.892 E.14896
G3 X113.755 Y105.371 I-1.625 J.486 E.02499
G1 X116.27 Y103.947 E.14883
G1 X116.339 Y104.427 E.02495
G1 X113.773 Y105.879 E.15186
G1 X113.727 Y106.424 E.02814
G1 X116.408 Y104.906 E.15865
G1 X116.476 Y105.386 E.02495
G1 X113.588 Y107.021 E.17093
G1 X113.377 Y107.572 E.03039
G1 X113.307 Y107.698 E.00746
G1 X116.522 Y105.878 E.19029
G1 X116.522 Y106.397 E.0267
G1 X112.759 Y108.527 E.22274
G3 X111.773 Y109.392 I-3.831 J-3.37 E.06772
G1 X111.575 Y109.498 E.01156
G1 X111.575 Y109.716 E.01119
G1 X116.522 Y106.915 E.29278
G1 X116.522 Y107.434 E.0267
G1 X111.575 Y110.234 E.29278
G1 X111.575 Y110.752 E.0267
G1 X116.522 Y107.952 E.29278
G1 X116.522 Y108.471 E.0267
G1 X111.575 Y111.271 E.29278
G1 X111.575 Y111.789 E.0267
G1 X116.522 Y108.989 E.29278
G1 X116.522 Y109.507 E.0267
G1 X111.575 Y112.308 E.29278
G1 X111.575 Y112.826 E.0267
G1 X115.514 Y110.597 E.23312
G3 X114.749 Y111.259 I-11.124 J-12.077 E.05215
G1 X114.896 Y111.465 E.01304
G1 X111.575 Y113.345 E.19656
G1 X111.575 Y113.863 E.0267
G1 X115.162 Y111.833 E.21225
G1 X115.427 Y112.201 E.02337
G1 X111.575 Y114.382 E.22795
G1 X111.575 Y114.9 E.0267
G1 X115.109 Y112.9 E.20915
G1 X115.06 Y112.966 E.00422
G1 X114.818 Y113.583 E.03416
G1 X111.373 Y115.533 E.20389
M106 S193.8
M204 S10000
G1 X111.764 Y119.671 F42000
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
; LAYER_HEIGHT: 0.2
G1 F8843.478
M204 S6000
G1 X113.392 Y119.671 E.05401
G1 X113.166 Y119.351 E.013
G3 X112.587 Y117.779 I.951 J-1.243 E.05866
G1 X112.957 Y117.255 E.02128
G2 X113.536 Y115.682 I-.951 J-1.243 E.05866
G2 X113.08 Y115.06 I-3.182 J1.853 E.02564
G1 X114.637 Y114.179 E.05934
G1 X114.684 Y114.634 E.01519
G1 X115.053 Y115.158 E.02128
G3 X115.633 Y116.731 I-.951 J1.243 E.05866
G1 X115.263 Y117.255 E.02128
G2 X114.684 Y118.827 I.951 J1.243 E.05866
G2 X115.334 Y119.671 I4.332 J-2.664 E.03542
G1 X116.544 Y119.671 E.04013
G1 X116.544 Y110.233 E.31308
G3 X115.351 Y111.305 I-18.025 J-18.85 E.05319
G3 X115.573 Y111.67 I-.322 J.445 E.01455
G1 X116.055 Y112.34 E.02736
G1 X115.578 Y112.986 E.02665
; WIPE_START
G1 X116.055 Y112.34 E-.30529
G1 X115.573 Y111.67 E-.31346
G1 X115.513 Y111.489 E-.07251
G1 X115.393 Y111.353 E-.06874
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.821 Y110.4 Z2.6 F42000
G1 X95.796 Y108.887 Z2.6
G1 Z2.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.426421
G1 F9387.198
M204 S6000
G2 X96.03 Y108.946 I.952 J-3.298 E.00755
; LINE_WIDTH: 0.389874
G1 F10376.011
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.34711
G1 F11834.705
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304346
G1 F13770.623
G1 X96.385 Y109.01 E.00257
; LINE_WIDTH: 0.261582
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.220745
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185201
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.1512
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.116375
G2 X97.473 Y109.102 I.477 J-6.534 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.1505
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185183
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219181
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259129
G1 X98.564 Y109.01 E.00237
; LINE_WIDTH: 0.304342
G1 F13770.848
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.347109
G1 F11834.744
G1 X98.802 Y108.967 E.00299
; LINE_WIDTH: 0.389877
G1 F10375.943
G1 X98.92 Y108.946 E.00341
; LINE_WIDTH: 0.426419
G1 F9387.263
G2 X99.154 Y108.887 I-.714 J-3.339 E.00755
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.134117
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.108301
G1 X100.065 Y108.46 E.001
M204 S10000
G1 X100.793 Y108.215 F42000
; FEATURE: Bridge
; LINE_WIDTH: 0.43328
; LAYER_HEIGHT: 0.4
M106 S255
G1 F3000
M204 S6000
G1 X105.652 Y107.71 E.29347
G3 X105.46 Y107.276 I1.424 J-.888 E.02858
G1 X105.449 Y107.245 E.00199
G1 X101.319 Y107.675 E.24946
G2 X101.532 Y107.167 I-2.813 J-1.478 E.03313
G1 X105.301 Y106.774 E.22764
G1 X105.205 Y106.298 E.02916
G1 X101.672 Y106.666 E.21341
G2 X101.752 Y106.172 I-1.679 J-.524 E.03017
G1 X105.175 Y105.816 E.20677
G3 X105.199 Y105.327 I4.106 J-.041 E.02939
G1 X101.777 Y105.683 E.2067
G1 X101.742 Y105.201 E.02905
G1 X105.278 Y104.833 E.21355
G3 X105.418 Y104.333 I1.81 J.236 E.03132
G1 X101.648 Y104.725 E.22768
G2 X101.502 Y104.254 I-1.772 J.293 E.0297
G1 X105.632 Y103.825 E.24943
G1 X105.895 Y103.35 E.03261
G1 X105.523 Y103.35 E.0224
G1 X101.081 Y103.812 E.26829
M106 S193.8
; WIPE_START
G1 X103.07 Y103.605 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z2.6 F42000
G1 Z2.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.1083
; LAYER_HEIGHT: 0.2
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134107
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.426403
G1 F9387.636
M204 S6000
G2 X98.92 Y102.554 I-.945 J3.266 E.00756
; LINE_WIDTH: 0.389839
G1 F10377.067
G1 X98.801 Y102.533 E.0034
; LINE_WIDTH: 0.34708
G1 F11835.907
G1 X98.683 Y102.511 E.00298
; LINE_WIDTH: 0.30432
G1 F13772.023
G1 X98.565 Y102.49 E.00256
; LINE_WIDTH: 0.259116
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219178
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185171
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150479
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.116351
G1 X97.473 Y102.398 E.00286
G2 X96.992 Y102.415 I-.004 J6.552 E.00288
; LINE_WIDTH: 0.151159
G1 X96.834 Y102.432 E.0014
; LINE_WIDTH: 0.185143
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.220673
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.261542
G1 X96.386 Y102.49 E.00215
; LINE_WIDTH: 0.304341
G1 F13770.89
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347141
G1 F11833.518
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.389941
G1 F10374.036
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426463
G1 F9386.172
G2 X95.796 Y102.613 I.715 J3.345 E.00755
M204 S10000
G1 X94.733 Y103.839 F42000
; LINE_WIDTH: 0.106669
G1 F15000
M204 S6000
G1 X94.649 Y103.936 E.00067
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497435
G1 F7920.534
M204 S6000
G1 X94.419 Y105.024 E.00999
; LINE_WIDTH: 0.46323
G1 F8565.111
G2 X94.389 Y105.321 I4.132 J.58 E.01023
; LINE_WIDTH: 0.429919
G1 F9302.364
G2 X94.391 Y106.208 I8.941 J.423 E.028
; LINE_WIDTH: 0.464985
G1 F8529.5
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.497409
G1 F7920.998
G1 X94.448 Y106.744 E.00999
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.106645
G1 F15000
M204 S6000
G2 X94.649 Y107.564 I.126 J.005 E.00052
G1 X94.732 Y107.66 E.00066
; CHANGE_LAYER
; Z_HEIGHT: 2.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F15000
G1 X94.649 Y107.564 E-.43237
G1 X94.615 Y107.473 E-.32763
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 12/79
; update layer progress
M73 L12
M991 S0 P11 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z2.6 I.05 J1.216 P1  F42000
G1 X99.722 Y107.262 Z2.6
G1 Z2.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.527 Y107.528 E.01095
G3 X97.332 Y103.049 I-2.045 J-1.776 E.35417
G3 X99.524 Y103.974 I.136 J2.735 E.08165
G3 X99.761 Y107.216 I-2.043 J1.779 E.11565
M204 S10000
G1 X99.396 Y107.018 F42000
G1 F8843.478
M204 S6000
G1 X99.219 Y107.262 E.00999
G3 X97.361 Y103.455 I-1.736 J-1.51 E.30094
G3 X98.72 Y103.812 I.106 J2.357 E.04734
G3 X99.434 Y106.972 I-1.237 J1.94 E.11921
M204 S250
G1 X99.087 Y106.786 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.389 Y103.846 I-1.603 J-1.035 E.23973
G3 X98.269 Y104.012 I.104 J1.855 E.02777
G3 X99.118 Y106.735 I-.785 J1.739 E.099
; WIPE_START
M204 S6000
G1 X98.919 Y107.001 E-.12641
G1 X98.726 Y107.194 E-.10358
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10357
G1 X97.747 Y107.641 E-.10358
G1 X97.475 Y107.661 E-.1036
G1 X97.443 Y107.658 E-.01209
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X95.407 Y102.903 E.00899
G2 X94.798 Y103.45 I1.6 J2.389 E.02724
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.605 Y102.683 E.00385
; WIPE_START
G1 X95.407 Y102.903 E-.11226
G1 X95.165 Y103.084 E-.11485
G1 X94.798 Y103.45 E-.19686
G1 X94.798 Y102.573 E-.33322
G1 X94.806 Y102.573 E-.00281
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01718
G1 X95.575 Y108.724 E.01703
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29243
G1 X94.798 Y108.05 E-.33323
G1 X94.905 Y108.156 E-.05713
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z2.8 F42000
G1 X106.692 Y108.52 Z2.8
G1 Z2.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21185
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.312 J-2.128 E.14915
G1 X100.306 Y102.98 E.02659
G1 X106.65 Y102.98 E.21044
G1 X106.186 Y103.588 E.02537
G2 X106.651 Y108.477 I3.311 J2.152 E.17578
; WIPE_START
G1 X104.651 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.622 Y108.76 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.566 Y108.927 E.00584
G1 X99.382 Y108.927 E.27148
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18577
G2 X99.327 Y102.74 I-3.357 J2.283 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.572 Y102.573 E.27168
G1 X107.627 Y102.742 E.00588
G2 X107.385 Y108.582 I1.865 J3.003 E.2283
G1 X107.574 Y108.724 E.00783
; WIPE_START
G1 X107.566 Y108.927 E-.07722
G1 X105.769 Y108.927 E-.68278
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.618 Y108.645 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.324 Y108.752 E.01039
G3 X109.229 Y102.647 I-.842 J-3 E.34453
G3 X111.851 Y103.729 I.26 J3.09 E.09775
G3 X110.751 Y108.598 I-2.369 J2.023 E.19205
G1 X110.675 Y108.625 E.00268
M204 S10000
G1 X110.485 Y108.261 F42000
G1 F8843.478
M204 S6000
G1 X110.449 Y108.281 E.00136
G3 X109.255 Y103.053 I-.967 J-2.53 E.30747
G3 X111.269 Y103.717 I.21 J2.753 E.07223
G3 X110.583 Y108.226 I-1.787 J2.035 E.17986
G1 X110.542 Y108.241 E.00147
M204 S10000
G1 X110.376 Y107.859 F42000
G1 F8843.478
M204 S6000
G1 X110.309 Y107.898 E.00257
G3 X109.281 Y103.459 I-.826 J-2.147 E.26101
G3 X110.449 Y103.662 I.212 J2.242 E.03979
G3 X110.704 Y107.701 I-.965 J2.088 E.16404
G1 X110.43 Y107.833 E.01008
M204 S250
G1 X110.205 Y107.509 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.175 Y107.529 E.0011
G3 X109.306 Y103.851 I-.69 J-1.779 E.20038
G3 X110.03 Y103.922 I.161 J2.074 E.02248
G3 X110.494 Y107.369 I-.546 J1.828 E.13446
G1 X110.259 Y107.483 E.00805
; WIPE_START
M204 S6000
G1 X110.175 Y107.529 E-.03637
G1 X109.996 Y107.588 E-.07148
G1 X109.73 Y107.643 E-.1034
G1 X109.458 Y107.66 E-.10324
G1 X109.185 Y107.638 E-.10411
G1 X108.92 Y107.578 E-.10341
G1 X108.665 Y107.481 E-.10361
G1 X108.428 Y107.348 E-.1032
G1 X108.363 Y107.298 E-.03118
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.258 Y102.98 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.14089
G1 X116.93 Y105.943 E.09927
G1 X116.93 Y120.02 E.46696
G1 X111.205 Y120.02 E.18989
G1 X111.205 Y109.277 E.35636
G2 X112.423 Y108.358 I-1.912 J-3.799 E.05088
G2 X112.3 Y103.023 I-2.951 J-2.6 E.19452
; WIPE_START
G1 X114.299 Y103.003 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.378 Y102.573 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18324
G1 X116.902 Y102.88 E.01018
G1 X117.337 Y105.914 E.10166
G1 X117.337 Y120.427 E.48142
G1 X110.798 Y120.427 E.2169
G1 X110.798 Y109.013 E.37861
G1 X110.918 Y108.969 E.00425
M73 P51 R11
G2 X111.33 Y102.756 I-1.448 J-3.216 E.25308
G1 X111.363 Y102.631 E.00426
; WIPE_START
G1 X113.362 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.732 Y102.432 Z2.8 F42000
G1 X94.391 Y102.166 Z2.8
G1 Z2.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.744 Y105.885 E.10166
G1 X117.744 Y120.704 E.4916
G1 X117.701 Y120.834 E.00452
G1 X110.391 Y120.834 E.24249
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.962 E.07869
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00427
G2 X94.637 Y104.454 I2.834 J-1.296 E.56078
G1 X94.592 Y104.575 E.00427
G1 X94.391 Y104.538 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z2.8 F42000
G1 X61.755 Y60.52 Z2.8
G1 Z2.4
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X118.151 Y105.856 E.10166
G1 X118.151 Y120.77 E.49473
G1 X117.995 Y121.241 E.01645
G1 X109.984 Y121.241 E.26575
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.558 Y105.827 E.10166
G1 X118.558 Y120.835 E.49787
G1 X118.29 Y121.648 E.02839
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
M73 P52 R11
G1 X118.515 Y102.765 E1.37673
G1 X118.95 Y105.799 E.09417
G1 X118.95 Y120.898 E.46398
G1 X118.573 Y122.04 E.03694
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z2.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z2.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z2.8 F4000
            G39.3 S1
            G0 Z2.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z2.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z2.8 F42000
G1 X61.959 Y60.25 Z2.8
G1 Z2.4
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.086 Y103.372 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X113.424 Y103.98 E.02135
G3 X113.638 Y106.915 I-4.094 J1.774 E.09216
G1 X113.401 Y107.572 E.02146
G3 X112.804 Y108.505 I-3.593 J-1.643 E.03415
G1 X112.29 Y109.038 E.02275
G1 X111.793 Y109.405 E.01898
G1 X111.597 Y109.512 E.00684
G1 X111.597 Y114.709 E.15968
G1 X112.72 Y114.709 E.0345
G2 X112.732 Y111.896 I-69.767 J-1.69 E.08643
G1 X112.8 Y111.728 E.00557
G2 X114.292 Y110.583 I-5.093 J-8.181 E.0579
G2 X116.228 Y106.751 I-4.91 J-4.886 E.13414
G1 X116.28 Y106.657 E.00329
G1 X116.538 Y106.559 E.00848
G2 X116.469 Y105.492 I-4.242 J-.263 E.03295
G1 X116.165 Y103.372 E.06578
G1 X113.146 Y103.372 E.09275
M204 S10000
G1 X113.729 Y103.75 F42000
; LINE_WIDTH: 0.420314
G1 F9539.101
M204 S6000
G1 X113.99 Y104.427 E.02234
G1 X114.132 Y105.083 E.02064
G1 X114.179 Y105.742 E.02031
G1 X114.131 Y106.421 E.02095
G1 X114.006 Y106.998 E.01815
G1 X113.753 Y107.707 E.02313
G1 X113.436 Y108.286 E.02031
G1 X113.104 Y108.733 E.01712
G1 X112.554 Y109.307 E.02445
G1 X111.974 Y109.735 E.02216
G2 X111.975 Y111.896 I584.617 J.877 E.06645
G1 X111.975 Y114.331 E.07488
G1 X112.354 Y114.331 E.01164
G1 X112.354 Y111.896 E.07488
G1 X112.473 Y111.539 E.01157
G1 X112.681 Y111.332 E.00902
G1 X113.356 Y110.887 E.02487
G1 X113.991 Y110.346 E.02566
G2 X115.816 Y106.879 I-4.683 J-4.678 E.12232
M73 P53 R11
G1 X115.953 Y106.461 E.01352
G1 X116.161 Y106.303 E.00803
G1 X116.161 Y106.034 E.0083
G2 X115.838 Y103.749 I-241.05 J32.869 E.07094
G1 X113.789 Y103.749 E.06303
M204 S10000
G1 X114.282 Y104.127 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G3 X114.555 Y105.719 I-5.075 J1.691 E.04982
G1 X114.507 Y106.451 E.02256
G3 X112.352 Y109.931 I-5.079 J-.739 E.12935
G1 X112.352 Y111.146 E.03735
G1 X112.493 Y111.005 E.00613
G1 X113.135 Y110.582 E.02364
G1 X113.739 Y110.065 E.02442
G2 X115.447 Y106.801 I-4.337 J-4.347 E.11498
G1 X115.491 Y106.594 E.00649
G1 X115.646 Y106.242 E.01183
G1 X115.784 Y106.101 E.00604
G1 X115.784 Y106.034 E.00209
G2 X115.511 Y104.127 I-763.997 J108.103 E.05919
G1 X114.342 Y104.127 E.03594
M204 S10000
G1 X114.784 Y104.505 F42000
; LINE_WIDTH: 0.428104
G1 F9346.191
M204 S6000
G3 X114.947 Y105.883 I-8.034 J1.652 E.04359
; LINE_WIDTH: 0.43794
G1 F9113.463
G1 X114.914 Y106.081 E.00648
; LINE_WIDTH: 0.40386
G1 F9973.957
G1 X114.882 Y106.28 E.00592
; LINE_WIDTH: 0.349962
G1 F11724.787
G3 X114.53 Y107.693 I-7.745 J-1.178 E.03648
G3 X112.693 Y110.103 I-5.018 J-1.918 E.07688
G1 X112.693 Y110.48 E.00942
G2 X115.114 Y106.73 I-3.208 J-4.728 E.11473
; LINE_WIDTH: 0.364547
G1 F11193.102
G1 X115.183 Y106.493 E.00648
; LINE_WIDTH: 0.40072
G1 F10061.488
G1 X115.252 Y106.255 E.0072
; LINE_WIDTH: 0.431588
G1 F9262.409
G1 X115.321 Y106.018 E.00783
G1 X115.374 Y105.953 E.00265
G2 X115.183 Y104.505 I-27.366 J2.869 E.04625
G1 X114.844 Y104.505 E.01074
; WIPE_START
G1 X115.183 Y104.505 E-.12884
G1 X115.374 Y105.953 E-.5549
G1 X115.321 Y106.018 E-.03174
G1 X115.288 Y106.131 E-.04452
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.094 Y102.853 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.430481
G1 F9288.87
M204 S6000
G1 X110.968 Y102.565 E.00993
G1 X110.944 Y102.559 E.00077
; LINE_WIDTH: 0.400766
G1 F10060.195
G1 X110.828 Y102.538 E.00346
; LINE_WIDTH: 0.35757
G1 F11441.286
G1 X110.711 Y102.516 E.00304
; LINE_WIDTH: 0.314374
G1 F13261.917
G1 X110.594 Y102.495 E.00262
; LINE_WIDTH: 0.268549
G1 F15000
G1 X110.463 Y102.471 E.00245
; LINE_WIDTH: 0.227483
G1 X110.305 Y102.453 E.00239
; LINE_WIDTH: 0.191994
G1 X110.147 Y102.435 E.00193
; LINE_WIDTH: 0.155754
G1 X109.982 Y102.417 E.00153
; LINE_WIDTH: 0.116978
G1 X109.507 Y102.398 E.00287
G2 X109.015 Y102.414 I-.022 J6.926 E.00297
; LINE_WIDTH: 0.155488
G1 X108.782 Y102.438 E.00215
; LINE_WIDTH: 0.203469
G1 X108.549 Y102.462 E.00307
; LINE_WIDTH: 0.229304
G1 X108.536 Y102.464 E.0002
; LINE_WIDTH: 0.25197
G1 X108.417 Y102.485 E.00205
; LINE_WIDTH: 0.293619
G1 F14359.887
G1 X108.299 Y102.506 E.00246
; LINE_WIDTH: 0.335267
G1 F12314.132
G1 X108.18 Y102.526 E.00287
; LINE_WIDTH: 0.376916
G1 F10778.583
G1 X108.062 Y102.547 E.00328
; LINE_WIDTH: 0.418886
G1 F9575.335
G2 X107.799 Y102.612 I.794 J3.784 E.00829
M204 S10000
G1 X107.135 Y102.777 F42000
; LINE_WIDTH: 0.117911
G1 F15000
M204 S6000
G1 X106.91 Y103.016 E.00201
; WIPE_START
G1 X107.135 Y102.777 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.87 Y108.659 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
; LINE_WIDTH: 0.421908
G1 F9498.987
M204 S6000
G1 X107.983 Y108.936 E.00924
G1 X107.998 Y108.939 E.00049
; LINE_WIDTH: 0.403243
G1 F9991.054
G1 X108.117 Y108.961 E.00354
; LINE_WIDTH: 0.359339
G1 F11377.324
G1 X108.235 Y108.983 E.00311
; LINE_WIDTH: 0.315436
G1 F13210.266
G1 X108.354 Y109.005 E.00268
; LINE_WIDTH: 0.271532
G1 F15000
G1 X108.472 Y109.027 E.00225
; LINE_WIDTH: 0.229296
G1 X108.644 Y109.047 E.00263
; LINE_WIDTH: 0.192364
G1 X108.801 Y109.064 E.00193
; LINE_WIDTH: 0.157122
G1 X108.958 Y109.082 E.00147
; LINE_WIDTH: 0.11703
G2 X109.45 Y109.102 I.513 J-6.658 E.00297
G1 X109.921 Y109.087 E.00284
; LINE_WIDTH: 0.153503
G1 X110.162 Y109.063 E.00219
; LINE_WIDTH: 0.20259
G1 X110.398 Y109.038 E.00308
; LINE_WIDTH: 0.242751
G1 X110.595 Y109.005 E.00325
; WIPE_START
G1 X110.398 Y109.038 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.124 Y114.339 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X113.124 Y112.711 E.05401
G2 X113.675 Y111.606 I-1.104 J-1.241 E.04197
G2 X114.688 Y110.73 I-4.503 J-6.23 E.04449
G1 X114.817 Y110.965 E.00891
G3 X115.787 Y112.538 I-.981 J1.69 E.06383
G1 X115.499 Y113.062 E.01983
G2 X114.53 Y114.634 I.981 J1.69 E.06383
G1 X114.817 Y115.158 E.01983
G3 X115.787 Y116.731 I-.981 J1.69 E.06383
G1 X115.499 Y117.255 E.01983
G2 X114.53 Y118.827 I.981 J1.69 E.06383
G2 X115.185 Y119.671 I1.475 J-.468 E.03621
G1 X113.578 Y119.671 E.0533
G1 X113.403 Y119.351 E.01212
G3 X112.433 Y117.779 I.981 J-1.69 E.06383
G1 X112.721 Y117.255 E.01983
G2 X113.69 Y115.682 I-.981 J-1.69 E.06383
G2 X113.094 Y114.889 I-1.375 J.414 E.0336
G1 X112.883 Y115.101 E.00991
G1 X111.554 Y115.101 E.04408
G1 X111.554 Y116.425 E.04393
G3 X111.554 Y116.804 I-.258 J.189 E.01343
G1 X111.554 Y118.432 E.05401
; WIPE_START
G1 X111.554 Y116.804 E-.61876
G1 X111.594 Y116.731 E-.03165
G1 X111.556 Y116.445 E-.10959
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.288 Y112.089 Z2.8 F42000
G1 X100.065 Y108.46 Z2.8
G1 Z2.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108293
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.001
; LINE_WIDTH: 0.134108
G1 X99.82 Y108.723 E.00128
M204 S10000
G1 X99.154 Y108.887 F42000
; LINE_WIDTH: 0.426419
G1 F9387.26
M204 S6000
G3 X98.92 Y108.946 I-.954 J-3.307 E.00755
; LINE_WIDTH: 0.389878
G1 F10375.919
G1 X98.802 Y108.967 E.00341
; LINE_WIDTH: 0.347112
G1 F11834.643
G1 X98.683 Y108.989 E.00299
; LINE_WIDTH: 0.304347
G1 F13770.618
G1 X98.565 Y109.01 E.00257
; LINE_WIDTH: 0.259135
G1 F15000
G1 X98.432 Y109.034 E.00237
; LINE_WIDTH: 0.219181
G1 X98.274 Y109.051 E.00228
; LINE_WIDTH: 0.185183
G1 X98.116 Y109.068 E.00184
; LINE_WIDTH: 0.1505
G1 X97.951 Y109.085 E.00145
; LINE_WIDTH: 0.11637
G1 X97.473 Y109.102 E.00286
G3 X96.992 Y109.085 I-.003 J-6.555 E.00288
; LINE_WIDTH: 0.1512
G1 X96.834 Y109.068 E.0014
; LINE_WIDTH: 0.185198
G1 X96.676 Y109.051 E.00184
; LINE_WIDTH: 0.220742
G1 X96.504 Y109.032 E.00251
; LINE_WIDTH: 0.261582
G1 X96.385 Y109.01 E.00215
; LINE_WIDTH: 0.304346
G1 F13770.623
G1 X96.267 Y108.989 E.00257
; LINE_WIDTH: 0.34711
G1 F11834.705
G1 X96.148 Y108.967 E.00299
; LINE_WIDTH: 0.389874
G1 F10376.011
G1 X96.03 Y108.946 E.00341
; LINE_WIDTH: 0.426417
G1 F9387.309
G3 X95.796 Y108.887 I.706 J-3.309 E.00755
M204 S10000
G1 X94.732 Y107.66 F42000
; LINE_WIDTH: 0.106646
G1 F15000
M204 S6000
G1 X94.649 Y107.564 E.00067
G3 X94.615 Y107.473 I.093 J-.086 E.00052
M204 S10000
G1 X94.448 Y106.744 F42000
; LINE_WIDTH: 0.49743
G1 F7920.633
M204 S6000
G1 X94.419 Y106.476 E.00999
; LINE_WIDTH: 0.465008
G1 F8529.039
G1 X94.391 Y106.208 E.00927
; LINE_WIDTH: 0.429919
G1 F9302.349
G3 X94.389 Y105.321 I8.938 J-.464 E.028
; LINE_WIDTH: 0.463247
G1 F8564.774
G3 X94.419 Y105.024 I4.171 J.284 E.01023
; LINE_WIDTH: 0.497444
G1 F7920.374
G1 X94.448 Y104.756 E.00999
M204 S10000
G1 X94.615 Y104.027 F42000
; LINE_WIDTH: 0.106645
G1 F15000
M204 S6000
G3 X94.649 Y103.937 I.126 J-.005 E.00052
G1 X94.732 Y103.839 E.00067
M204 S10000
G1 X95.796 Y102.613 F42000
; LINE_WIDTH: 0.426405
G1 F9387.603
M204 S6000
G3 X96.03 Y102.554 I.95 J3.293 E.00755
; LINE_WIDTH: 0.389878
G1 F10375.919
G1 X96.148 Y102.533 E.00341
; LINE_WIDTH: 0.347112
G1 F11834.643
G1 X96.267 Y102.511 E.00299
; LINE_WIDTH: 0.304347
G1 F13770.618
G1 X96.385 Y102.49 E.00257
; LINE_WIDTH: 0.261581
G1 F15000
G1 X96.504 Y102.468 E.00215
; LINE_WIDTH: 0.220723
G1 X96.676 Y102.449 E.00251
; LINE_WIDTH: 0.185173
G1 X96.834 Y102.432 E.00184
; LINE_WIDTH: 0.151169
G1 X96.992 Y102.415 E.0014
; LINE_WIDTH: 0.116351
G3 X97.473 Y102.398 I.477 J6.538 E.00288
G1 X97.951 Y102.415 E.00286
; LINE_WIDTH: 0.150487
G1 X98.116 Y102.432 E.00145
; LINE_WIDTH: 0.185159
G1 X98.274 Y102.449 E.00184
; LINE_WIDTH: 0.219145
G1 X98.432 Y102.466 E.00228
; LINE_WIDTH: 0.259086
G1 X98.564 Y102.49 E.00237
; LINE_WIDTH: 0.304314
G1 F13772.323
G1 X98.683 Y102.511 E.00257
; LINE_WIDTH: 0.347097
G1 F11835.241
G1 X98.802 Y102.533 E.00299
; LINE_WIDTH: 0.389879
G1 F10375.871
G1 X98.92 Y102.554 E.00341
; LINE_WIDTH: 0.426433
G1 F9386.923
G3 X99.154 Y102.613 I-.709 J3.319 E.00755
M204 S10000
G1 X99.82 Y102.777 F42000
; LINE_WIDTH: 0.134094
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.00128
; LINE_WIDTH: 0.108297
G1 X100.065 Y103.04 E.001
; WIPE_START
G1 X99.942 Y102.899 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X101.089 Y103.372 Z2.8 F42000
G1 Z2.4
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X101.406 Y103.94 E.01997
G3 X101.632 Y106.957 I-4.111 J1.824 E.09481
G3 X101.089 Y108.128 I-4.069 J-1.174 E.03981
G1 X105.864 Y108.128 E.14671
G1 X105.532 Y107.533 E.02092
G3 X105.186 Y105.223 I3.875 J-1.761 E.0727
G1 X105.33 Y104.505 E.02249
G3 X105.859 Y103.372 I4.19 J1.267 E.03855
G1 X101.149 Y103.372 E.14471
M204 S10000
G1 X101.732 Y103.75 F42000
G1 F9547.299
M204 S6000
G1 X101.977 Y104.386 E.02095
G1 X102.126 Y105.041 E.02063
G3 X102 Y107.037 I-5.365 J.665 E.06181
G2 X101.743 Y107.751 I14.692 J5.692 E.02331
G1 X105.221 Y107.751 E.10685
G1 X104.96 Y107.07 E.02241
G1 X104.818 Y106.417 E.02052
G3 X104.962 Y104.422 I5.411 J-.613 E.06181
G1 X105.218 Y103.75 E.02211
G1 X101.792 Y103.75 E.10527
M204 S10000
G1 X102.283 Y104.127 F42000
G1 F9547.299
M204 S6000
G1 X102.494 Y104.96 E.02643
G1 X102.552 Y105.642 E.02103
G1 X102.518 Y106.346 E.02166
G1 X102.368 Y107.117 E.02412
G1 X102.283 Y107.373 E.00831
G1 X104.669 Y107.373 E.07332
G3 X104.434 Y105.163 I4.618 J-1.608 E.06889
G1 X104.594 Y104.338 E.02583
G1 X104.665 Y104.127 E.00686
G1 X102.343 Y104.127 E.07135
M204 S10000
G1 X102.781 Y104.504 F42000
G1 F9547.299
M204 S6000
G3 X102.781 Y106.996 I-5.096 J1.246 E.07733
G1 X104.168 Y106.996 E.04264
G3 X104.17 Y104.504 I5.232 J-1.243 E.0773
G1 X102.841 Y104.504 E.04085
M204 S10000
G1 X103.253 Y104.89 F42000
; LINE_WIDTH: 0.424458
G1 F9435.503
M204 S6000
G3 X103.252 Y106.611 I-9.891 J.853 E.05359
G1 X103.698 Y106.611 E.01386
G3 X103.697 Y104.89 I10.052 J-.863 E.05358
G1 X103.313 Y104.89 E.01194
; CHANGE_LAYER
; Z_HEIGHT: 2.6
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9435.503
G1 X103.697 Y104.89 E-.14597
G1 X103.673 Y105.103 E-.08157
G1 X103.655 Y105.872 E-.2922
G1 X103.691 Y106.503 E-.24025
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 13/79
; update layer progress
M73 L13
M991 S0 P12 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z2.8 I-.203 J-1.2 P1  F42000
G1 X99.784 Y107.166 Z2.8
G1 Z2.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.76 Y107.219 E.00192
G3 X97.347 Y103.047 I-2.277 J-1.466 E.36746
G3 X99.251 Y103.701 I.144 J2.681 E.06843
G3 X99.946 Y106.878 I-1.768 J2.052 E.11575
G1 X99.813 Y107.114 E.00896
M204 S10000
G1 X99.396 Y107.018 F42000
G1 F8843.478
M204 S6000
G1 X99.283 Y107.185 E.0067
G3 X97.376 Y103.453 I-1.8 J-1.433 E.30478
G3 X98.72 Y103.812 I.089 J2.364 E.04684
G3 X99.434 Y106.972 I-1.237 J1.94 E.1192
M204 S250
G1 X99.087 Y106.786 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G3 X97.404 Y103.845 I-1.604 J-1.034 E.2403
G3 X98.269 Y104.012 I.088 J1.858 E.02732
G3 X99.118 Y106.735 I-.786 J1.739 E.09898
; WIPE_START
M204 S6000
G1 X98.961 Y106.944 E-.09942
G1 X98.726 Y107.194 E-.13035
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10357
G1 X97.747 Y107.641 E-.10358
G1 X97.475 Y107.661 E-.1036
G1 X97.443 Y107.658 E-.01231
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z3 F42000
G1 Z2.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X95.418 Y102.894 E.0085
G2 X94.798 Y103.45 I1.628 J2.438 E.02773
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.418 Y102.894 E-.10673
G1 X95.165 Y103.084 E-.12045
G1 X94.798 Y103.45 E-.19689
G1 X94.798 Y102.573 E-.33322
G1 X94.805 Y102.573 E-.00272
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z3 F42000
G1 Z2.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01719
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29242
G1 X94.798 Y108.05 E-.33322
G1 X94.905 Y108.156 E-.05714
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z3 F42000
G1 X106.692 Y108.52 Z3
G1 Z2.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21185
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.311 J-2.128 E.14915
G1 X100.306 Y102.98 E.02659
G1 X106.65 Y102.98 E.21046
G1 X106.187 Y103.587 E.02531
G2 X106.65 Y108.477 I3.31 J2.153 E.17585
; WIPE_START
G1 X104.65 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.622 Y108.76 Z3 F42000
G1 Z2.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.566 Y108.927 E.00584
G1 X99.382 Y108.927 E.27147
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18577
G2 X99.327 Y102.74 I-3.356 J2.283 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.572 Y102.573 E.27169
G1 X107.627 Y102.742 E.00588
G2 X107.396 Y108.59 I1.865 J3.003 E.22875
G1 X107.574 Y108.724 E.00738
; WIPE_START
G1 X107.566 Y108.927 E-.07722
G1 X105.769 Y108.927 E-.68278
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.612 Y108.647 Z3 F42000
G1 Z2.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.322 Y108.752 E.01024
G3 X109.215 Y102.648 I-.84 J-3 E.34404
G3 X111.853 Y103.731 I.253 J3.14 E.09818
G3 X110.75 Y108.598 I-2.371 J2.021 E.19201
G1 X110.669 Y108.627 E.00284
M204 S10000
G1 X110.48 Y108.263 F42000
G1 F8843.478
M204 S6000
G1 X110.459 Y108.27 E.00073
G3 X109.241 Y103.054 I-.984 J-2.52 E.30756
G3 X110.734 Y103.355 I.227 J2.732 E.05122
G3 X110.579 Y108.219 I-1.259 J2.395 E.20079
G1 X110.535 Y108.239 E.00159
M204 S10000
G1 X110.372 Y107.862 F42000
G1 F8843.478
M204 S6000
G1 X110.322 Y107.893 E.00197
G3 X109.267 Y103.46 I-.839 J-2.142 E.26106
G3 X110.45 Y103.663 I.224 J2.245 E.04031
G3 X110.702 Y107.702 I-.967 J2.088 E.16403
G1 X110.426 Y107.836 E.01017
M204 S250
G1 X110.2 Y107.513 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X110.187 Y107.523 E.0005
G3 X109.292 Y103.851 I-.704 J-1.773 E.2004
G3 X110.031 Y103.922 I.174 J2.08 E.02296
G3 X110.492 Y107.368 I-.548 J1.827 E.13438
G1 X110.254 Y107.486 E.00818
; WIPE_START
M204 S6000
G1 X110.187 Y107.523 E-.0289
G1 X109.995 Y107.588 E-.07717
G1 X109.728 Y107.644 E-.10347
G1 X109.457 Y107.66 E-.10317
G1 X109.184 Y107.638 E-.1041
G1 X108.919 Y107.578 E-.10346
G1 X108.664 Y107.48 E-.10356
G1 X108.427 Y107.347 E-.10321
G1 X108.358 Y107.295 E-.03295
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.258 Y102.98 Z3 F42000
G1 Z2.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.14089
G1 X116.968 Y106.207 E.10811
G1 X116.968 Y120.02 E.45821
G1 X111.205 Y120.02 E.19115
G1 X111.205 Y109.277 E.35637
G2 X112.421 Y108.359 I-1.911 J-3.799 E.0508
G2 X112.3 Y103.023 I-2.949 J-2.602 E.19461
; WIPE_START
G1 X114.3 Y103.003 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.378 Y102.573 Z3 F42000
G1 Z2.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18324
G1 X116.902 Y102.88 E.01018
G1 X117.375 Y106.177 E.1105
G1 X117.375 Y120.427 E.47267
G1 X110.798 Y120.427 E.21815
G1 X110.798 Y109.013 E.3786
G1 X110.917 Y108.969 E.00419
G2 X111.33 Y102.756 I-1.446 J-3.217 E.25315
G1 X111.362 Y102.631 E.00426
; WIPE_START
G1 X113.362 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.732 Y102.432 Z3 F42000
G1 X94.391 Y102.166 Z3
G1 Z2.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.782 Y106.148 E.1105
G1 X117.782 Y120.59 E.47905
G1 X117.701 Y120.834 E.00852
G1 X110.391 Y120.834 E.24249
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.962 E.07869
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00428
G2 X94.637 Y104.454 I2.834 J-1.296 E.56076
G1 X94.592 Y104.575 E.00428
G1 X94.391 Y104.539 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z3 F42000
G1 X61.755 Y60.52 Z3
G1 Z2.6
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X118.189 Y106.119 E.1105
G1 X118.189 Y120.655 E.48218
G1 X117.995 Y121.241 E.02046
G1 X109.984 Y121.241 E.26575
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.596 Y106.09 E.1105
G1 X118.596 Y120.721 E.48532
G1 X118.29 Y121.648 E.03239
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X118.988 Y106.062 E.10235
G1 X118.988 Y120.784 E.45235
G1 X118.573 Y122.04 E.04065
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z3 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z3
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z3 F4000
            G39.3 S1
            G0 Z3 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z2.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z3 F42000
G1 X61.959 Y60.25 Z3
G1 Z2.6
M73 P54 R11
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z3 F42000
G1 Z2.6
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.576 Y106.259 Z3 F42000
G1 Z2.6
G1 E.8 F1800
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G2 X116.165 Y103.372 I-241.214 J32.832 E.08959
G1 X113.086 Y103.372 E.09461
G1 X113.425 Y103.982 E.02143
G3 X113.638 Y106.914 I-4.095 J1.772 E.09205
G1 X113.4 Y107.575 E.0216
G3 X112.804 Y108.504 I-3.587 J-1.644 E.03403
G1 X112.287 Y109.04 E.02288
G1 X111.79 Y109.407 E.01898
G1 X111.597 Y109.512 E.00673
G1 X111.597 Y114.711 E.15976
G3 X112.72 Y114.709 I.845 J124.842 E.0345
G2 X112.732 Y111.896 I-69.766 J-1.69 E.08643
G1 X112.8 Y111.728 E.00557
G2 X114.292 Y110.583 I-5.093 J-8.182 E.0579
G2 X116.235 Y106.72 I-4.954 J-4.912 E.1351
G1 X116.353 Y106.582 E.00555
G1 X116.576 Y106.532 E.00703
G1 X116.576 Y106.319 E.00653
M204 S10000
G1 X116.196 Y106.247 F42000
; LINE_WIDTH: 0.420313
G1 F9539.13
M204 S6000
G1 X115.838 Y103.749 E.0776
G1 X113.729 Y103.75 E.06488
G1 X113.991 Y104.431 E.02245
G1 X114.132 Y105.087 E.02065
G3 X114.006 Y106.998 I-5.215 J.615 E.05922
G1 X113.752 Y107.71 E.02327
G1 X113.435 Y108.289 E.02029
G1 X113.104 Y108.733 E.01702
G1 X112.551 Y109.31 E.02458
G1 X112.013 Y109.711 E.02065
G1 X111.974 Y109.787 E.0026
G2 X111.975 Y111.896 I570.73 J.852 E.06487
G1 X111.975 Y114.331 E.07488
G1 X112.354 Y114.331 E.01164
G1 X112.354 Y111.896 E.07488
G1 X112.473 Y111.539 E.01157
G1 X112.681 Y111.332 E.00902
G1 X113.356 Y110.887 E.02487
G1 X113.991 Y110.346 E.02566
G2 X115.815 Y106.882 I-4.687 J-4.68 E.1222
G1 X115.956 Y106.434 E.01445
G1 X116.149 Y106.284 E.00752
M204 S10000
G1 X115.795 Y106.103 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X115.511 Y104.127 E.06136
G1 X114.282 Y104.127 E.03778
G3 X114.555 Y105.722 I-5.073 J1.691 E.04992
G1 X114.509 Y106.419 E.02148
G3 X112.352 Y109.93 I-5.073 J-.699 E.13031
G1 X112.352 Y111.146 E.03736
G1 X112.493 Y111.005 E.00613
G1 X113.135 Y110.582 E.02364
G1 X113.739 Y110.065 E.02442
G2 X115.446 Y106.804 I-4.338 J-4.348 E.11486
G3 X115.647 Y106.218 I1.541 J.201 E.01916
G1 X115.748 Y106.14 E.00391
M204 S10000
G1 X115.374 Y105.952 F42000
; LINE_WIDTH: 0.428461
G1 F9337.531
M204 S6000
G2 X115.183 Y104.505 I-28.42 J3.026 E.04586
G1 X114.784 Y104.505 E.01253
G3 X114.943 Y105.885 I-7.411 J1.556 E.0437
; LINE_WIDTH: 0.42443
G1 F9436.188
G1 X114.898 Y106.166 E.00884
; LINE_WIDTH: 0.37805
G1 F10742.099
G1 X114.852 Y106.447 E.00776
; LINE_WIDTH: 0.349623
G1 F11737.753
G1 X114.707 Y107.158 E.01814
G3 X112.693 Y110.103 I-5.325 J-1.48 E.09082
G1 X112.693 Y110.48 E.00941
G2 X115.113 Y106.733 I-3.209 J-4.728 E.11451
; LINE_WIDTH: 0.363237
G1 F11238.878
G1 X115.18 Y106.494 E.0065
; LINE_WIDTH: 0.39699
G1 F10167.481
G1 X115.247 Y106.254 E.00718
; LINE_WIDTH: 0.432781
G1 F9234.079
G1 X115.313 Y106.014 E.0079
G1 X115.332 Y105.995 E.00086
M204 S10000
G1 X116.619 Y107.063 F42000
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.619 Y108.691 E.05401
G2 X116.409 Y109.393 I.334 J.483 E.02625
G1 X116.619 Y109.899 E.0182
G1 X116.619 Y112.884 E.099
G2 X116.409 Y113.586 I.334 J.483 E.02625
G1 X116.619 Y114.092 E.0182
G1 X116.619 Y117.077 E.099
G2 X116.409 Y117.779 I.334 J.483 E.02625
G1 X116.619 Y118.285 E.0182
G1 X116.619 Y119.671 E.04597
G1 X114.952 Y119.671 E.05531
G1 X114.342 Y119.351 E.02285
G3 X114.312 Y118.827 I.393 J-.286 E.0184
G3 X114.976 Y117.779 I1.964 J.509 E.04183
G1 X115.974 Y117.255 E.0374
G2 X116.004 Y116.731 I-.393 J-.286 E.0184
G2 X115.34 Y115.682 I-1.964 J.509 E.04182
G1 X114.342 Y115.158 E.0374
G3 X114.312 Y114.634 I.393 J-.286 E.0184
G3 X114.976 Y113.586 I1.964 J.509 E.04182
G1 X115.974 Y113.062 E.0374
G2 X116.004 Y112.538 I-.393 J-.286 E.0184
G2 X115.34 Y111.489 I-1.964 J.509 E.04182
G1 X114.412 Y111.002 E.03478
G2 X113.69 Y112.013 I.73 J1.285 E.04256
G1 X113.244 Y112.538 E.02282
G1 X113.124 Y112.601 E.00451
G1 X113.124 Y114.762 E.0717
G1 X113.877 Y115.158 E.02824
G3 X113.908 Y115.682 I-.393 J.286 E.0184
G3 X113.244 Y116.731 I-1.964 J-.509 E.04182
G1 X112.246 Y117.255 E.0374
G2 X112.216 Y117.779 I.393 J.286 E.0184
G2 X112.879 Y118.827 I1.964 J-.509 E.04183
G1 X113.877 Y119.351 E.0374
G3 X113.956 Y119.671 I-.21 J.221 E.01155
G1 X111.554 Y119.671 E.07969
G1 X111.554 Y117.401 E.07532
G2 X111.811 Y116.731 I-.184 J-.455 E.0267
G1 X111.554 Y116.16 E.02076
G1 X111.554 Y115.174 E.03272
G1 X111.657 Y115.101 E.0042
G1 X112.16 Y115.101 E.01667
; WIPE_START
G1 X111.657 Y115.101 E-.19101
G1 X111.554 Y115.174 E-.04815
G1 X111.554 Y116.16 E-.37481
G1 X111.712 Y116.51 E-.14604
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.595 Y109.005 Z3 F42000
G1 Z2.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.242494
G1 F15000
M204 S6000
G1 X110.396 Y109.039 E.00328
; LINE_WIDTH: 0.20207
G1 X110.16 Y109.063 E.00308
; LINE_WIDTH: 0.153067
G1 X109.918 Y109.087 E.00218
; LINE_WIDTH: 0.117044
G1 X109.448 Y109.102 E.00284
G3 X108.956 Y109.082 I.029 J-6.805 E.00297
; LINE_WIDTH: 0.157517
G1 X108.799 Y109.064 E.00148
; LINE_WIDTH: 0.192911
G1 X108.642 Y109.046 E.00193
; LINE_WIDTH: 0.230004
G1 X108.47 Y109.027 E.00264
; LINE_WIDTH: 0.272363
G1 X108.351 Y109.005 E.00225
; LINE_WIDTH: 0.316367
G1 F13165.257
G1 X108.233 Y108.983 E.00269
; LINE_WIDTH: 0.360372
G1 F11340.309
G1 X108.114 Y108.961 E.00312
; LINE_WIDTH: 0.415586
G1 F9660.135
G1 X107.982 Y108.936 E.00407
G1 X107.869 Y108.66 E.00905
; WIPE_START
G1 X107.982 Y108.936 E-.52444
G1 X108.114 Y108.961 E-.23556
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X106.912 Y103.014 Z3 F42000
G1 Z2.6
G1 E.8 F1800
; LINE_WIDTH: 0.117653
G1 F15000
M204 S6000
G1 X107.136 Y102.777 E.00198
M204 S10000
G1 X107.799 Y102.612 F42000
; LINE_WIDTH: 0.41828
G1 F9590.799
M204 S6000
G3 X108.064 Y102.547 I1.051 J3.694 E.00835
; LINE_WIDTH: 0.375822
G1 F10814.019
G1 X108.183 Y102.526 E.00326
; LINE_WIDTH: 0.334264
G1 F12356.54
G1 X108.301 Y102.505 E.00286
; LINE_WIDTH: 0.292706
G1 F14412.33
G1 X108.42 Y102.484 E.00245
; LINE_WIDTH: 0.251149
G1 F15000
G1 X108.539 Y102.463 E.00204
; LINE_WIDTH: 0.228541
G1 X108.552 Y102.462 E.0002
; LINE_WIDTH: 0.202824
G1 X108.785 Y102.438 E.00305
; LINE_WIDTH: 0.155071
G1 X109.018 Y102.414 E.00214
; LINE_WIDTH: 0.117017
G3 X109.509 Y102.398 I.463 J6.771 E.00297
G1 X109.985 Y102.417 E.00288
; LINE_WIDTH: 0.156273
G1 X110.15 Y102.436 E.00153
; LINE_WIDTH: 0.192611
G1 X110.308 Y102.454 E.00194
; LINE_WIDTH: 0.228191
G1 X110.466 Y102.471 E.0024
; LINE_WIDTH: 0.269305
G1 X110.597 Y102.495 E.00246
; LINE_WIDTH: 0.315157
G1 F13223.775
G1 X110.713 Y102.517 E.00263
; LINE_WIDTH: 0.358369
G1 F11412.333
G1 X110.83 Y102.538 E.00304
; LINE_WIDTH: 0.40158
G1 F10037.376
G1 X110.946 Y102.56 E.00346
; LINE_WIDTH: 0.428986
G1 F9324.838
G1 X110.968 Y102.565 E.0007
G1 X111.094 Y102.854 E.00992
; WIPE_START
G1 X110.968 Y102.565 E-.7097
G1 X110.946 Y102.56 E-.0503
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X103.339 Y103.187 Z3 F42000
G1 X101.089 Y103.372 Z3
G1 Z2.6
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X101.406 Y103.94 E.01997
G3 X101.632 Y106.957 I-4.111 J1.824 E.0948
G3 X101.089 Y108.128 I-4.07 J-1.174 E.03981
G1 X105.864 Y108.128 E.14671
G1 X105.531 Y107.531 E.021
G3 X105.186 Y105.223 I3.872 J-1.758 E.07262
G1 X105.331 Y104.502 E.0226
G3 X105.859 Y103.372 I4.199 J1.275 E.03845
G1 X101.149 Y103.372 E.14471
M204 S10000
G1 X101.732 Y103.75 F42000
G1 F9547.299
M204 S6000
G1 X101.977 Y104.386 E.02096
G1 X102.126 Y105.041 E.02062
G3 X102 Y107.037 I-5.375 J.664 E.06181
G2 X101.743 Y107.751 I15.38 J5.943 E.02331
G1 X105.221 Y107.751 E.10686
G1 X104.959 Y107.067 E.02248
G1 X104.818 Y106.413 E.02057
G3 X104.963 Y104.418 I5.427 J-.607 E.0618
G1 X105.218 Y103.75 E.022
G1 X101.792 Y103.75 E.10527
M204 S10000
G1 X102.283 Y104.127 F42000
G1 F9547.299
M204 S6000
G1 X102.494 Y104.96 E.02643
G1 X102.552 Y105.639 E.02094
G1 X102.517 Y106.346 E.02175
G1 X102.368 Y107.117 E.02411
G1 X102.283 Y107.373 E.00831
G1 X104.669 Y107.373 E.07332
G3 X104.435 Y105.164 I4.627 J-1.609 E.06888
G1 X104.595 Y104.335 E.02595
G1 X104.665 Y104.127 E.00674
G1 X102.343 Y104.127 E.07135
M204 S10000
G1 X102.781 Y104.504 F42000
G1 F9547.299
M204 S6000
G3 X102.781 Y106.996 I-5.097 J1.246 E.07733
G1 X104.168 Y106.996 E.04264
G3 X104.17 Y104.504 I5.238 J-1.243 E.07729
G1 X102.841 Y104.504 E.04085
M204 S10000
G1 X103.253 Y104.89 F42000
; LINE_WIDTH: 0.42448
G1 F9434.951
M204 S6000
G3 X103.252 Y106.611 I-9.919 J.852 E.05359
G1 X103.698 Y106.611 E.01387
G3 X103.697 Y104.89 I10.113 J-.863 E.05359
G1 X103.313 Y104.89 E.01194
; WIPE_START
G1 X103.697 Y104.89 E-.14593
G1 X103.674 Y105.103 E-.0816
G1 X103.655 Y105.872 E-.29224
G1 X103.691 Y106.503 E-.24023
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z3 F42000
G1 Z2.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108303
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134102
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.426471
G1 F9385.993
M204 S6000
G2 X98.92 Y102.554 I-.938 J3.241 E.00755
; LINE_WIDTH: 0.389952
G1 F10373.702
G1 X98.802 Y102.533 E.00341
; LINE_WIDTH: 0.34716
G1 F11832.781
G1 X98.683 Y102.511 E.00299
; LINE_WIDTH: 0.304368
G1 F13769.482
G1 X98.565 Y102.49 E.00257
; LINE_WIDTH: 0.259126
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219161
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185169
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150491
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.116351
G1 X97.473 Y102.398 E.00286
G2 X96.992 Y102.415 I-.003 J6.555 E.00288
; LINE_WIDTH: 0.151159
M73 P55 R11
G1 X96.834 Y102.432 E.0014
; LINE_WIDTH: 0.185143
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.220673
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.261544
G1 X96.386 Y102.49 E.00215
; LINE_WIDTH: 0.304349
G1 F13770.494
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347153
G1 F11833.031
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.389958
G1 F10373.513
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426473
G1 F9385.935
G2 X95.796 Y102.613 I.712 J3.332 E.00755
M204 S10000
G1 X94.733 Y103.839 F42000
; LINE_WIDTH: 0.106676
G1 F15000
M204 S6000
G1 X94.649 Y103.936 E.00067
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497407
G1 F7921.022
M204 S6000
G1 X94.419 Y105.024 E.00999
; LINE_WIDTH: 0.463222
G1 F8565.275
G2 X94.389 Y105.321 I4.139 J.581 E.01022
; LINE_WIDTH: 0.429919
G1 F9302.364
G2 X94.391 Y106.208 I8.941 J.423 E.02799
; LINE_WIDTH: 0.464985
G1 F8529.5
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.497409
G1 F7920.998
G1 X94.448 Y106.744 E.00999
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.10665
G1 F15000
M204 S6000
G2 X94.649 Y107.563 I.126 J.005 E.00052
G1 X94.732 Y107.661 E.00067
M204 S10000
G1 X95.796 Y108.887 F42000
; LINE_WIDTH: 0.426421
G1 F9387.198
M204 S6000
G2 X96.03 Y108.946 I.952 J-3.298 E.00755
; LINE_WIDTH: 0.389874
G1 F10376.011
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.34711
G1 F11834.705
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304346
G1 F13770.623
G1 X96.385 Y109.01 E.00257
; LINE_WIDTH: 0.261582
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.220742
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185198
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.1512
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.11637
G2 X97.473 Y109.102 I.477 J-6.538 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.1505
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185183
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219181
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259135
G1 X98.565 Y109.01 E.00237
; LINE_WIDTH: 0.304347
G1 F13770.618
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.347112
G1 F11834.643
G1 X98.802 Y108.967 E.00299
; LINE_WIDTH: 0.389878
G1 F10375.919
G1 X98.92 Y108.946 E.00341
; LINE_WIDTH: 0.426419
G1 F9387.262
G2 X99.154 Y108.887 I-.717 J-3.355 E.00755
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.134088
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.108285
G1 X100.065 Y108.46 E.001
; CHANGE_LAYER
; Z_HEIGHT: 2.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F15000
G1 X99.942 Y108.601 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 14/79
; update layer progress
M73 L14
M991 S0 P13 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z3 I1.201 J-.197 P1  F42000
G1 X99.722 Y107.262 Z3
G1 Z2.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.527 Y107.528 E.01095
G3 X97.362 Y103.046 I-2.045 J-1.776 E.35513
G3 X99.251 Y103.701 I.128 J2.683 E.06794
G3 X99.761 Y107.216 I-1.768 J2.052 E.12853
M204 S10000
G1 X99.396 Y107.018 F42000
G1 F8843.478
M204 S6000
G1 X99.212 Y107.255 E.00996
G3 X95.794 Y107.318 I-1.737 J-1.505 E.12786
G3 X97.391 Y103.452 I1.681 J-1.568 E.17425
G3 X99.425 Y106.966 I.083 J2.297 E.16503
M204 S250
G1 X99.082 Y106.783 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X98.921 Y107.003 E.00838
G3 X97.419 Y103.843 I-1.439 J-1.253 E.23233
G3 X98.269 Y104.012 I.071 J1.866 E.02686
G3 X99.115 Y106.737 I-.787 J1.738 E.09904
; WIPE_START
M204 S6000
G1 X98.921 Y107.003 E-.12516
G1 X98.726 Y107.194 E-.10367
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10357
G1 X97.747 Y107.641 E-.10358
G1 X97.475 Y107.661 E-.10359
G1 X97.44 Y107.658 E-.01326
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X95.43 Y102.885 E.008
G2 X94.798 Y103.45 I1.65 J2.481 E.02822
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.43 Y102.885 E-.10117
G1 X95.164 Y103.084 E-.12622
G1 X94.798 Y103.45 E-.19679
G1 X94.798 Y102.573 E-.33321
G1 X94.805 Y102.573 E-.0026
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01718
G1 X95.575 Y108.724 E.01703
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29244
G1 X94.798 Y108.05 E-.33322
G1 X94.905 Y108.156 E-.05712
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z3.2 F42000
G1 X106.692 Y108.52 Z3.2
G1 Z2.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21185
G1 X100.786 Y107.878 E.0266
G2 X100.786 Y103.622 I-3.311 J-2.128 E.14915
G1 X100.306 Y102.98 E.02659
G1 X106.651 Y102.98 E.21048
G1 X106.188 Y103.584 E.02524
G2 X106.65 Y108.477 I3.309 J2.155 E.17593
; WIPE_START
G1 X104.65 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.621 Y108.76 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.566 Y108.927 E.00584
G1 X99.382 Y108.927 E.27147
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18577
G2 X99.327 Y102.74 I-3.357 J2.283 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.573 Y102.573 E.27169
G1 X107.627 Y102.742 E.00588
G2 X107.407 Y108.599 I1.865 J3.003 E.22921
G1 X107.573 Y108.724 E.00691
; WIPE_START
G1 X107.566 Y108.927 E-.07722
G1 X105.769 Y108.927 E-.68278
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.606 Y108.649 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.32 Y108.753 E.01009
G3 X109.2 Y102.649 I-.839 J-3.001 E.34354
G3 X111.855 Y103.732 I.268 J3.137 E.09874
G3 X110.748 Y108.599 I-2.373 J2.019 E.192
G1 X110.663 Y108.629 E.00298
M204 S10000
G1 X110.547 Y108.229 F42000
G1 F8843.478
M204 S6000
G1 X110.472 Y108.264 E.00275
G3 X109.227 Y103.055 I-.997 J-2.515 E.30758
G3 X110.723 Y103.348 I.24 J2.74 E.05124
G3 X110.913 Y108.041 I-1.247 J2.401 E.18868
G1 X110.601 Y108.202 E.01165
M204 S10000
G1 X110.369 Y107.866 F42000
G1 F8843.478
M204 S6000
G1 X110.335 Y107.888 E.00136
G3 X109.253 Y103.461 I-.853 J-2.137 E.26116
G3 X110.451 Y103.664 I.236 J2.248 E.04082
G3 X110.7 Y107.703 I-.969 J2.087 E.16401
G1 X110.423 Y107.839 E.01026
M204 S250
G1 X110.195 Y107.517 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X109.993 Y107.587 E.00658
G3 X109.278 Y103.852 I-.511 J-1.838 E.19377
G3 X110.033 Y103.923 I.186 J2.088 E.02342
G3 X110.251 Y107.495 I-.551 J1.826 E.14266
; WIPE_START
M204 S6000
G1 X109.993 Y107.587 E-.10402
G1 X109.727 Y107.644 E-.10346
G1 X109.456 Y107.66 E-.10313
G1 X109.183 Y107.638 E-.10412
G1 X108.917 Y107.577 E-.10347
G1 X108.663 Y107.479 E-.10357
G1 X108.426 Y107.347 E-.10316
G1 X108.353 Y107.291 E-.03506
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.258 Y102.98 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.14088
G1 X117.005 Y106.47 E.11695
G1 X117.005 Y120.02 E.44946
G1 X111.205 Y120.02 E.1924
G1 X111.205 Y109.276 E.35637
G2 X112.42 Y108.361 I-1.91 J-3.798 E.05073
G2 X112.3 Y103.023 I-2.947 J-2.604 E.19468
; WIPE_START
G1 X114.3 Y103.003 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.377 Y102.573 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18325
G1 X116.902 Y102.88 E.01018
G1 X117.413 Y106.441 E.11934
G1 X117.413 Y120.427 E.46392
G1 X110.798 Y120.427 E.21941
G1 X110.798 Y109.013 E.3786
G1 X110.915 Y108.97 E.00412
G2 X111.33 Y102.756 I-1.443 J-3.217 E.25324
G1 X111.362 Y102.631 E.00426
; WIPE_START
G1 X113.362 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.732 Y102.432 Z3.2 F42000
G1 X94.391 Y102.166 Z3.2
G1 Z2.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.82 Y106.412 E.11934
G1 X117.82 Y120.475 E.4665
G1 X117.701 Y120.834 E.01253
G1 X110.391 Y120.834 E.24249
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.962 E.07869
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00427
G2 X94.637 Y104.454 I2.834 J-1.296 E.56078
G1 X94.592 Y104.575 E.00427
G1 X94.391 Y104.538 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z3.2 F42000
G1 X61.755 Y60.52 Z3.2
G1 Z2.8
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X118.227 Y106.383 E.11934
G1 X118.227 Y120.541 E.46963
G1 X117.995 Y121.241 E.02446
G1 X109.984 Y121.241 E.26575
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.634 Y106.354 E.11934
G1 X118.634 Y120.606 E.47277
G1 X118.29 Y121.648 E.03639
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X119.026 Y106.326 E.11054
G1 X119.026 Y120.669 E.44072
G1 X118.573 Y122.04 E.04436
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z3.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z3.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z3.2 F4000
            G39.3 S1
            G0 Z3.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z2.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z3.2 F42000
G1 X61.959 Y60.25 Z3.2
G1 Z2.8
G1 E.8 F1800
; LINE_WIDTH: 0.17516
M73 P55 R10
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.574 Y107.011 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.588 Y106.943 E.00229
G1 X116.657 Y106.982 E.00261
G1 X116.657 Y108.451 E.04873
G1 X116.243 Y108.242 E.01539
G3 X115.755 Y109.286 I-7.955 J-3.082 E.03827
G1 X116.206 Y109.514 E.01678
G1 X116.657 Y110.07 E.02376
M73 P56 R10
G1 X116.657 Y111.699 E.05401
M204 S10000
G1 X116.657 Y115.208 F42000
G1 F8843.478
M204 S6000
G1 X116.657 Y116.837 E.05401
G1 X116.206 Y116.61 E.01674
G2 X114.634 Y115.539 I-1.81 J.969 E.0656
G1 X114.11 Y115.803 E.01947
G3 X112.537 Y116.874 I-1.81 J-.969 E.0656
G1 X111.975 Y116.562 E.02133
G1 X112.013 Y117.9 E.04439
G2 X113.586 Y118.97 I1.81 J-.969 E.0656
G1 X114.11 Y118.706 E.01947
G3 X115.682 Y117.636 I1.81 J.969 E.0656
G1 X116.206 Y117.9 E.01947
G1 X116.657 Y118.457 E.02376
G1 X116.657 Y119.671 E.0403
G1 X116.244 Y119.671 E.01371
M204 S10000
G1 X111.591 Y119.634 F42000
; Slow Down Start
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.405503
G1 F3000;_EXTRUDE_SET_SPEED
M204 S6000
G1 X111.59 Y115.05 E.13545
; Slow Down End
M204 S10000
G1 X116.613 Y106.5 F42000
; LINE_WIDTH: 0.419765
G1 F9553.019
M204 S6000
G1 X116.165 Y103.372 E.09703
G1 X113.086 Y103.372 E.09455
G1 X113.426 Y103.984 E.02149
G3 X113.638 Y106.916 I-4.095 J1.769 E.09199
G1 X113.398 Y107.578 E.02163
G3 X111.597 Y109.512 I-4.01 J-1.929 E.08238
G1 X111.59 Y114.99 E.16822
G3 X111.864 Y114.709 I.37 J.086 E.01267
G1 X112.72 Y114.709 E.02629
G2 X112.732 Y111.896 I-69.767 J-1.69 E.08638
G1 X112.8 Y111.728 E.00556
G2 X114.292 Y110.583 I-5.092 J-8.18 E.05786
G2 X116.227 Y106.743 I-4.837 J-4.845 E.13429
G1 X116.377 Y106.563 E.00723
G1 X116.555 Y106.516 E.00565
M204 S10000
G1 X116.198 Y106.257 F42000
; LINE_WIDTH: 0.420313
G1 F9539.133
M204 S6000
G1 X115.838 Y103.75 E.07791
G1 X113.728 Y103.749 E.06488
G1 X113.992 Y104.434 E.02256
G1 X114.133 Y105.091 E.02064
G3 X114.005 Y107 I-5.222 J.61 E.05918
G1 X113.75 Y107.714 E.02331
G1 X113.433 Y108.291 E.02026
G1 X113.104 Y108.732 E.01692
G1 X112.548 Y109.312 E.0247
G1 X112.01 Y109.713 E.02064
G1 X111.974 Y109.783 E.00241
G2 X111.975 Y111.896 I581.181 J.85 E.06499
G1 X111.975 Y114.331 E.07488
G1 X112.354 Y114.331 E.01164
G1 X112.354 Y111.896 E.07488
G1 X112.473 Y111.539 E.01157
G1 X112.681 Y111.332 E.00902
G1 X113.356 Y110.887 E.02486
G1 X113.991 Y110.346 E.02566
G2 X115.813 Y106.882 I-4.572 J-4.615 E.12225
G1 X115.951 Y106.453 E.01388
G1 X116.14 Y106.274 E.008
M204 S10000
G1 X115.791 Y106.074 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X115.511 Y104.127 E.06045
G1 X114.282 Y104.127 E.03779
G3 X114.555 Y105.725 I-5.037 J1.685 E.05003
G1 X114.506 Y106.449 E.0223
G3 X112.352 Y109.93 I-5.077 J-.735 E.1294
G1 X112.352 Y111.146 E.03736
G1 X112.493 Y111.005 E.00614
G1 X113.135 Y110.582 E.02364
G1 X113.739 Y110.065 E.02442
G2 X115.443 Y106.805 I-4.325 J-4.336 E.1148
G1 X115.488 Y106.59 E.00676
G1 X115.645 Y106.233 E.01197
G1 X115.75 Y106.118 E.00479
M204 S10000
G1 X115.373 Y105.948 F42000
; LINE_WIDTH: 0.42866
G1 F9332.727
M204 S6000
G2 X115.183 Y104.505 I-27.657 J2.918 E.04575
G1 X114.784 Y104.505 E.01253
G3 X114.945 Y105.888 I-7.593 J1.581 E.04382
; LINE_WIDTH: 0.425315
G1 F9414.349
G1 X114.896 Y106.182 E.00928
; LINE_WIDTH: 0.375945
G1 F10809.999
G1 X114.848 Y106.476 E.00809
; LINE_WIDTH: 0.349426
G1 F11745.31
G3 X112.693 Y110.103 I-5.415 J-.764 E.10818
G1 X112.693 Y110.48 E.0094
G2 X115.111 Y106.736 I-3.176 J-4.704 E.11439
; LINE_WIDTH: 0.362525
G1 F11263.903
G1 X115.179 Y106.498 E.00646
; LINE_WIDTH: 0.397515
G1 F10152.426
G1 X115.247 Y106.259 E.00717
; LINE_WIDTH: 0.434936
G1 F9183.299
G1 X115.336 Y105.995 E.0089
; WIPE_START
G1 X115.247 Y106.259 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.094 Y102.852 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.427364
G1 F9364.187
M204 S6000
G1 X110.968 Y102.565 E.00983
G1 X110.948 Y102.56 E.00063
; LINE_WIDTH: 0.402524
G1 F10011.017
G1 X110.832 Y102.539 E.00347
; LINE_WIDTH: 0.359272
G1 F11379.753
G1 X110.716 Y102.517 E.00305
; LINE_WIDTH: 0.316019
G1 F13182.042
G1 X110.599 Y102.495 E.00263
; LINE_WIDTH: 0.270106
G1 F15000
G1 X110.468 Y102.472 E.00246
; LINE_WIDTH: 0.228889
G1 X110.31 Y102.454 E.00241
; LINE_WIDTH: 0.193198
G1 X110.152 Y102.436 E.00195
; LINE_WIDTH: 0.156745
G1 X109.987 Y102.418 E.00154
; LINE_WIDTH: 0.117021
G1 X109.511 Y102.398 E.00288
G2 X109.02 Y102.414 I-.024 J6.982 E.00296
; LINE_WIDTH: 0.154657
G1 X108.787 Y102.438 E.00213
; LINE_WIDTH: 0.202219
G1 X108.554 Y102.461 E.00304
; LINE_WIDTH: 0.227831
G1 X108.541 Y102.463 E.0002
; LINE_WIDTH: 0.250373
G1 X108.423 Y102.484 E.00203
; LINE_WIDTH: 0.291826
G1 F14463.293
G1 X108.304 Y102.505 E.00244
; LINE_WIDTH: 0.33328
G1 F12398.419
G1 X108.186 Y102.525 E.00285
; LINE_WIDTH: 0.374734
G1 F10849.478
G1 X108.067 Y102.546 E.00325
; LINE_WIDTH: 0.400862
G1 F10057.513
G1 X107.797 Y102.603 E.00807
M204 S10000
G1 X107.136 Y102.777 F42000
; LINE_WIDTH: 0.117454
G1 F15000
M204 S6000
G1 X106.914 Y103.012 E.00197
; WIPE_START
G1 X107.136 Y102.777 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.869 Y108.661 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
; LINE_WIDTH: 0.414323
G1 F9692.98
M204 S6000
G1 X107.982 Y108.936 E.00899
G1 X108.111 Y108.96 E.00397
; LINE_WIDTH: 0.361393
G1 F11303.944
G1 X108.23 Y108.982 E.00313
; LINE_WIDTH: 0.317292
G1 F13120.884
G1 X108.348 Y109.004 E.0027
; LINE_WIDTH: 0.273191
G1 F15000
G1 X108.467 Y109.026 E.00226
; LINE_WIDTH: 0.230691
G1 X108.639 Y109.046 E.00265
; LINE_WIDTH: 0.193427
G1 X108.796 Y109.064 E.00194
; LINE_WIDTH: 0.157876
G1 X108.954 Y109.082 E.00148
; LINE_WIDTH: 0.117077
G2 X109.446 Y109.102 I.516 J-6.638 E.00297
G1 X109.915 Y109.088 E.00284
; LINE_WIDTH: 0.15265
G1 X110.158 Y109.063 E.00218
; LINE_WIDTH: 0.20153
G1 X110.394 Y109.039 E.00307
; LINE_WIDTH: 0.242225
G1 X110.595 Y109.004 E.00331
; WIPE_START
G1 X110.394 Y109.039 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.124 Y114.174 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X113.124 Y112.545 E.05401
G1 X113.586 Y112.258 E.01806
G1 X114.11 Y111.61 E.02763
G1 X114.634 Y111.346 E.01947
G3 X116.206 Y112.417 I-.238 J2.04 E.0656
G1 X116.657 Y112.644 E.01674
G1 X116.657 Y114.263 E.05373
G1 X116.206 Y113.707 E.02376
G1 X115.682 Y113.443 E.01947
G2 X114.11 Y114.513 I.238 J2.04 E.0656
G1 X113.586 Y114.777 E.01947
G1 X113.124 Y114.692 E.01559
G1 X113.124 Y114.86 E.00556
G1 X112.883 Y115.101 E.01131
G1 X111.975 Y115.101 E.03011
G1 X111.975 Y115.313 E.00704
; WIPE_START
G1 X111.975 Y115.101 E-.08061
G1 X112.883 Y115.101 E-.3449
G1 X113.124 Y114.86 E-.12954
G1 X113.124 Y114.692 E-.06372
G1 X113.489 Y114.759 E-.14124
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X106.58 Y111.517 Z3.2 F42000
G1 X100.065 Y108.46 Z3.2
G1 Z2.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108289
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.001
; LINE_WIDTH: 0.134107
G1 X99.82 Y108.723 E.00128
M204 S10000
G1 X99.154 Y108.887 F42000
; LINE_WIDTH: 0.426402
G1 F9387.664
M204 S6000
G3 X98.92 Y108.946 I-.938 J-3.239 E.00755
; LINE_WIDTH: 0.389859
G1 F10376.468
G1 X98.802 Y108.968 E.00341
; LINE_WIDTH: 0.347097
G1 F11835.231
G1 X98.683 Y108.989 E.00299
; LINE_WIDTH: 0.304335
G1 F13771.243
G1 X98.564 Y109.01 E.00257
; LINE_WIDTH: 0.259128
G1 F15000
G1 X98.432 Y109.034 E.00237
; LINE_WIDTH: 0.219181
G1 X98.274 Y109.051 E.00228
; LINE_WIDTH: 0.185183
G1 X98.116 Y109.068 E.00184
; LINE_WIDTH: 0.1505
G1 X97.951 Y109.085 E.00145
; LINE_WIDTH: 0.11637
G1 X97.473 Y109.102 E.00286
G3 X96.992 Y109.085 I-.003 J-6.555 E.00288
; LINE_WIDTH: 0.1512
G1 X96.834 Y109.068 E.0014
; LINE_WIDTH: 0.185201
G1 X96.676 Y109.051 E.00184
; LINE_WIDTH: 0.220745
G1 X96.504 Y109.032 E.00251
; LINE_WIDTH: 0.261585
G1 X96.385 Y109.01 E.00215
; LINE_WIDTH: 0.304353
G1 F13770.254
G1 X96.267 Y108.989 E.00257
; LINE_WIDTH: 0.347122
G1 F11834.249
G1 X96.148 Y108.967 E.00299
; LINE_WIDTH: 0.389891
G1 F10375.521
G1 X96.03 Y108.946 E.00341
; LINE_WIDTH: 0.426425
G1 F9387.121
G3 X95.796 Y108.887 I.72 J-3.367 E.00755
M204 S10000
G1 X94.732 Y107.66 F42000
; LINE_WIDTH: 0.106648
G1 F15000
M204 S6000
G1 X94.649 Y107.564 E.00067
G3 X94.615 Y107.473 I.093 J-.086 E.00052
M204 S10000
G1 X94.448 Y106.744 F42000
; LINE_WIDTH: 0.49743
G1 F7920.633
M204 S6000
G1 X94.419 Y106.476 E.00999
; LINE_WIDTH: 0.465008
G1 F8529.039
G1 X94.391 Y106.208 E.00927
; LINE_WIDTH: 0.429909
G1 F9302.588
G3 X94.389 Y105.321 I8.941 J-.464 E.02799
; LINE_WIDTH: 0.463227
G1 F8565.18
G3 X94.419 Y105.024 I4.167 J.283 E.01023
; LINE_WIDTH: 0.497425
G1 F7920.703
G1 X94.448 Y104.756 E.00999
M204 S10000
G1 X94.615 Y104.027 F42000
; LINE_WIDTH: 0.106656
G1 F15000
M204 S6000
G3 X94.649 Y103.936 I.126 J-.005 E.00052
G1 X94.732 Y103.839 E.00067
M204 S10000
G1 X95.796 Y102.613 F42000
; LINE_WIDTH: 0.426457
G1 F9386.333
M204 S6000
G3 X96.03 Y102.554 I.938 J3.242 E.00755
; LINE_WIDTH: 0.389921
G1 F10374.629
G1 X96.148 Y102.533 E.00341
; LINE_WIDTH: 0.347121
G1 F11834.276
G1 X96.267 Y102.511 E.00299
; LINE_WIDTH: 0.304322
G1 F13771.901
G1 X96.386 Y102.49 E.00257
; LINE_WIDTH: 0.261523
G1 F15000
G1 X96.504 Y102.468 E.00215
; LINE_WIDTH: 0.220674
G1 X96.676 Y102.449 E.00251
; LINE_WIDTH: 0.185143
G1 X96.834 Y102.432 E.00184
; LINE_WIDTH: 0.151159
G1 X96.992 Y102.415 E.0014
; LINE_WIDTH: 0.116351
G3 X97.473 Y102.398 I.477 J6.538 E.00288
G1 X97.951 Y102.415 E.00286
; LINE_WIDTH: 0.150494
G1 X98.116 Y102.432 E.00145
; LINE_WIDTH: 0.185179
G1 X98.274 Y102.449 E.00184
; LINE_WIDTH: 0.219178
G1 X98.432 Y102.466 E.00228
; LINE_WIDTH: 0.259119
G1 X98.565 Y102.49 E.00237
; LINE_WIDTH: 0.304334
G1 F13771.282
G1 X98.683 Y102.511 E.00257
; LINE_WIDTH: 0.347103
G1 F11834.997
G1 X98.802 Y102.533 E.00299
; LINE_WIDTH: 0.389872
G1 F10376.086
G1 X98.92 Y102.554 E.00341
; LINE_WIDTH: 0.426411
G1 F9387.442
G3 X99.154 Y102.613 I-.718 J3.358 E.00755
M204 S10000
G1 X99.82 Y102.777 F42000
; LINE_WIDTH: 0.134102
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.00128
; LINE_WIDTH: 0.108307
G1 X100.065 Y103.04 E.001
; WIPE_START
G1 X99.942 Y102.899 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X101.089 Y103.372 Z3.2 F42000
G1 Z2.8
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X101.406 Y103.94 E.01997
G3 X101.632 Y106.957 I-4.111 J1.824 E.09481
G3 X101.089 Y108.128 I-4.069 J-1.174 E.03981
G1 X105.864 Y108.128 E.14672
G1 X105.53 Y107.529 E.02107
G3 X105.186 Y105.224 I3.879 J-1.757 E.07252
G1 X105.332 Y104.499 E.02272
G3 X105.859 Y103.372 I4.211 J1.283 E.03835
G1 X101.149 Y103.372 E.14471
M204 S10000
G1 X101.732 Y103.75 F42000
G1 F9547.299
M204 S6000
G1 X101.977 Y104.386 E.02095
G1 X102.126 Y105.041 E.02063
G3 X102 Y107.037 I-5.385 J.663 E.06181
G2 X101.743 Y107.751 I15.112 J5.846 E.02331
G1 X105.221 Y107.751 E.10687
G1 X104.958 Y107.065 E.02256
G1 X104.817 Y106.409 E.0206
G3 X104.964 Y104.415 I5.44 J-.602 E.06179
G3 X105.218 Y103.75 I4.345 J1.279 E.02192
G1 X101.792 Y103.75 E.10527
M204 S10000
G1 X102.283 Y104.127 F42000
G1 F9547.299
M204 S6000
G1 X102.494 Y104.96 E.02643
G1 X102.552 Y105.636 E.02083
G1 X102.518 Y106.342 E.02171
G1 X102.368 Y107.117 E.02426
G1 X102.283 Y107.373 E.00831
G1 X104.669 Y107.373 E.07332
G3 X104.435 Y105.164 I4.634 J-1.609 E.06886
G1 X104.596 Y104.331 E.02608
G1 X104.665 Y104.127 E.00663
G1 X102.343 Y104.127 E.07134
M204 S10000
G1 X102.781 Y104.504 F42000
G1 F9547.299
M204 S6000
G3 X102.781 Y106.996 I-5.107 J1.246 E.07733
G1 X104.168 Y106.996 E.04263
G3 X104.17 Y104.504 I5.242 J-1.242 E.07729
G1 X102.841 Y104.504 E.04085
M204 S10000
G1 X103.253 Y104.89 F42000
; LINE_WIDTH: 0.424484
G1 F9434.87
M204 S6000
G3 X103.252 Y106.611 I-9.943 J.852 E.05359
G1 X103.698 Y106.611 E.01387
G3 X103.697 Y104.89 I10.167 J-.863 E.05359
G1 X103.313 Y104.89 E.01194
; CHANGE_LAYER
; Z_HEIGHT: 3
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9434.87
G1 X103.697 Y104.89 E-.14591
G1 X103.674 Y105.104 E-.08163
G1 X103.655 Y105.872 E-.29225
G1 X103.691 Y106.503 E-.24021
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 15/79
; update layer progress
M73 L15
M991 S0 P14 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z3.2 I-.228 J-1.195 P1  F42000
G1 X99.722 Y107.262 Z3.2
G1 Z3
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X99.526 Y107.528 E.01094
G3 X97.377 Y103.045 I-2.044 J-1.776 E.3556
G3 X99.251 Y103.701 I.112 J2.686 E.06744
G3 X99.76 Y107.216 I-1.769 J2.051 E.12851
M204 S10000
G1 X99.426 Y106.971 F42000
G1 F8843.478
M204 S6000
G1 X99.417 Y106.998 E.00096
G3 X97.406 Y103.451 I-1.933 J-1.247 E.31332
G3 X98.432 Y103.655 I.088 J2.249 E.03501
G3 X99.575 Y106.709 I-.948 J2.096 E.12025
G1 X99.456 Y106.918 E.00799
M204 S250
G1 X99.082 Y106.783 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X99.085 Y106.785 E.0001
G3 X97.434 Y103.842 I-1.602 J-1.036 E.24101
G3 X98.013 Y103.917 I.001 J2.282 E.018
G3 X99.216 Y106.545 I-.53 J1.832 E.1008
G1 X99.112 Y106.73 E.00653
; WIPE_START
M204 S6000
G1 X99.085 Y106.785 E-.02299
G1 X98.919 Y107.001 E-.10367
G1 X98.726 Y107.194 E-.1036
G1 X98.508 Y107.357 E-.10357
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10357
G1 X97.747 Y107.641 E-.10357
G1 X97.475 Y107.661 E-.10359
G1 X97.444 Y107.658 E-.01183
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y102.74 Z3.4 F42000
G1 Z3
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X94.798 Y103.45 I2.056 J3.225 E.03623
G1 X94.798 Y102.573 E.02909
G1 X95.568 Y102.573 E.02553
G1 X95.604 Y102.683 E.00385
; WIPE_START
G1 X95.165 Y103.084 E-.22606
G1 X94.798 Y103.45 E-.19683
G1 X94.798 Y102.573 E-.33322
G1 X94.809 Y102.573 E-.00389
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.623 Y108.76 Z3.4 F42000
G1 Z3
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X95.568 Y108.927 E.00584
G1 X94.798 Y108.927 E.02553
G1 X94.798 Y108.05 E.02909
G1 X95.165 Y108.416 E.01718
G1 X95.575 Y108.724 E.01702
; WIPE_START
G1 X95.568 Y108.927 E-.07722
G1 X94.798 Y108.927 E-.29242
G1 X94.798 Y108.05 E-.33322
G1 X94.905 Y108.156 E-.05714
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X102.533 Y108.391 Z3.4 F42000
G1 X106.692 Y108.52 Z3.4
G1 Z3
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X100.306 Y108.52 E.21185
G1 X100.786 Y107.878 E.02659
G2 X100.786 Y103.622 I-3.311 J-2.128 E.14916
G1 X100.306 Y102.98 E.02659
G1 X106.651 Y102.98 E.21049
G1 X106.19 Y103.583 E.02517
G2 X106.65 Y108.477 I3.308 J2.157 E.176
; WIPE_START
G1 X104.65 Y108.49 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.62 Y108.744 Z3.4 F42000
G1 Z3
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X107.572 Y108.927 E.00625
G1 X99.382 Y108.927 E.27169
G1 X99.327 Y108.76 E.00584
G2 X100.443 Y103.843 I-1.9 J-3.017 E.18578
G2 X99.327 Y102.74 I-3.356 J2.282 E.05237
G1 X99.382 Y102.573 E.00584
G1 X107.573 Y102.573 E.27169
G1 X107.628 Y102.742 E.00588
G2 X107.57 Y108.712 I1.857 J3.004 E.236
; WIPE_START
G1 X107.572 Y108.927 E-.08151
G1 X105.787 Y108.927 E-.6785
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.597 Y108.654 Z3.4 F42000
G1 Z3
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X110.318 Y108.754 E.00982
G3 X109.187 Y102.65 I-.836 J-3.002 E.34301
G3 X111.545 Y103.416 I.274 J3.167 E.08449
G3 X110.655 Y108.639 I-2.063 J2.336 E.2101
M204 S10000
G1 X110.545 Y108.232 F42000
G1 F8843.478
M204 S6000
G1 X110.485 Y108.26 E.00221
G3 X109.213 Y103.056 I-1.009 J-2.511 E.30759
G3 X110.711 Y103.342 I.251 J2.749 E.05125
G3 X110.911 Y108.042 I-1.236 J2.407 E.18921
G1 X110.598 Y108.204 E.01168
M204 S10000
G1 X110.322 Y107.887 F42000
G1 F8843.478
M204 S6000
G1 X110.098 Y107.966 E.0079
G3 X109.239 Y103.462 I-.614 J-2.217 E.25222
G3 X110.149 Y103.547 I.224 J2.51 E.03049
G3 X110.379 Y107.868 I-.666 J2.202 E.18682
M204 S250
G1 X110.19 Y107.518 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X109.991 Y107.587 E.00647
G3 X109.265 Y103.853 I-.508 J-1.839 E.19325
G3 X109.769 Y103.862 I.221 J1.774 E.01555
G3 X110.246 Y107.497 I-.286 J1.886 E.15123
; WIPE_START
M204 S6000
G1 X109.991 Y107.587 E-.10272
G1 X109.725 Y107.644 E-.10349
G1 X109.454 Y107.66 E-.10316
G1 X109.181 Y107.638 E-.10406
G1 X108.916 Y107.577 E-.10351
G1 X108.661 Y107.479 E-.10362
G1 X108.425 Y107.346 E-.1031
G1 X108.349 Y107.288 E-.03633
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X112.258 Y102.98 Z3.4 F42000
G1 Z3
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.505 Y102.98 E.14088
G1 X117.043 Y106.734 E.12579
G1 X117.043 Y120.02 E.44071
G1 X111.205 Y120.02 E.19366
G1 X111.205 Y109.276 E.35638
G2 X112.419 Y108.363 I-1.909 J-3.797 E.05066
G2 X112.3 Y103.023 I-2.943 J-2.606 E.19478
; WIPE_START
G1 X114.3 Y103.003 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.377 Y102.573 Z3.4 F42000
G1 Z3
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X116.902 Y102.573 E.18326
G1 X116.902 Y102.88 E.01018
G1 X117.45 Y106.705 E.12818
G1 X117.45 Y120.295 E.45081
G1 X117.407 Y120.427 E.0046
G1 X110.798 Y120.427 E.21922
G1 X110.798 Y109.014 E.3786
G1 X110.913 Y108.971 E.00405
G2 X111.33 Y102.756 I-1.44 J-3.218 E.25333
G1 X111.362 Y102.631 E.00426
; WIPE_START
G1 X113.362 Y102.61 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
M73 P57 R10
G1 X105.732 Y102.432 Z3.4 F42000
G1 X94.391 Y102.166 Z3.4
G1 Z3
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.309 Y102.166 E.76022
G1 X117.309 Y102.851 E.02272
G1 X117.857 Y106.676 E.12818
G1 X117.857 Y120.361 E.45394
G1 X117.701 Y120.834 E.01653
G1 X110.391 Y120.834 E.24249
G1 X110.391 Y109.334 E.38148
G1 X94.391 Y109.334 E.53075
G1 X94.391 Y106.962 E.07869
G1 X94.592 Y106.925 E.00677
G1 X94.637 Y107.046 E.00427
G2 X94.637 Y104.454 I2.834 J-1.296 E.56084
G1 X94.592 Y104.575 E.00428
G1 X94.391 Y104.539 E.00677
G1 X94.391 Y102.226 E.0767
; WIPE_START
G1 X96.391 Y102.221 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X91.515 Y96.35 Z3.4 F42000
G1 X61.755 Y60.52 Z3.4
G1 Z3
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.755 Y59.98 E.01789
G1 X116.495 Y59.98 E1.8158
G1 X116.495 Y60.52 E.01789
G1 X61.815 Y60.52 E1.81381
M204 S10000
G1 X61.348 Y60.927 F42000
G1 F8843.478
M204 S6000
G1 X61.348 Y59.573 E.0449
G1 X116.902 Y59.573 E1.84281
G1 X116.902 Y60.927 E.0449
G1 X61.408 Y60.927 E1.84082
M204 S10000
G1 X61.109 Y61.334 F42000
G1 F8843.478
M204 S6000
G1 X60.941 Y61.334 E.00556
G1 X60.941 Y59.166 E.0719
G1 X117.309 Y59.166 E1.86982
G1 X117.309 Y61.334 E.0719
G1 X61.169 Y61.334 E1.86227
M204 S10000
G1 X61.516 Y61.741 F42000
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.0615
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X117.716 Y58.759 E1.89682
G1 X117.716 Y102.822 E1.46165
G1 X118.265 Y106.647 E.12818
G1 X118.265 Y120.426 E.45708
G1 X117.995 Y121.241 E.02846
G1 X109.984 Y121.241 E.26575
G1 X109.984 Y109.741 E.38148
G1 X93.984 Y109.741 E.53075
G1 X93.984 Y101.759 E.26477
G1 X116.734 Y101.759 E.75466
G1 X116.734 Y61.741 E1.32748
G1 X61.576 Y61.741 E1.8297
M204 S10000
G1 X61.923 Y62.148 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.0615
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X118.123 Y58.352 E1.92383
G1 X118.123 Y102.793 E1.47419
G1 X118.672 Y106.618 E.12818
G1 X118.672 Y120.492 E.46022
G1 X118.29 Y121.648 E.0404
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y110.148 E.38148
G1 X93.577 Y110.148 E.53075
G1 X93.577 Y101.352 E.29178
G1 X116.327 Y101.352 E.75466
G1 X116.327 Y62.148 E1.30047
G1 X61.983 Y62.148 E1.80269
M204 S250
G1 X62.315 Y62.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X119.064 Y106.59 E.11873
G1 X119.064 Y120.555 E.4291
G1 X118.573 Y122.04 E.04807
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z3.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z3.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z3.4 F4000
            G39.3 S1
            G0 Z3.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y61.537 F42000
G1 Z3
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.49848
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.253 Y83.908 Z3.4 F42000
G1 X61.959 Y60.25 Z3.4
G1 Z3
G1 E.8 F1800
; LINE_WIDTH: 0.17516
G1 F15000
M204 S6000
G1 X116.291 Y60.25 E.58548
; WIPE_START
G1 X114.291 Y60.25 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y61.537 Z3.4 F42000
G1 Z3
G1 E.8 F1800
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y101.963 E1.89301
; WIPE_START
G1 X117.225 Y99.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.567 Y107.046 Z3.4 F42000
G1 Z3
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.596 Y106.909 E.00462
G1 X116.695 Y106.909 E.0033
G1 X116.695 Y108.299 E.0461
G1 X116.309 Y108.038 E.01547
G3 X115.681 Y109.414 I-6.889 J-2.313 E.05027
G3 X116.695 Y110.218 I-3.361 J5.282 E.04301
G1 X116.695 Y111.846 E.05401
M204 S10000
G1 X114.009 Y111.364 F42000
G1 F8843.478
M204 S6000
G3 X113.124 Y111.965 I-6.757 J-8.996 E.0355
G1 X113.124 Y112.522 E.01848
G1 X113.586 Y112.347 E.01639
G3 X114.634 Y111.511 I3.308 J3.071 E.04465
G3 X116.206 Y112.162 I.253 J1.613 E.05938
G1 X116.695 Y112.492 E.01957
G1 X116.695 Y114.411 E.06365
G2 X115.682 Y113.607 I-3.182 J2.97 E.04305
G2 X114.11 Y114.258 I-.253 J1.613 E.05938
M73 P58 R10
G1 X113.586 Y114.613 E.02099
G1 X113.124 Y114.638 E.01536
G1 X113.124 Y114.86 E.00734
G1 X112.883 Y115.101 E.01131
G1 X112.127 Y115.101 E.02507
G1 X112.127 Y115.411 E.0103
M204 S10000
G1 X111.666 Y114.99 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.557853
G1 F6991.205
M204 S6000
G1 X111.666 Y119.427 E.1862
G1 X111.68 Y119.545 E.00498
; LINE_WIDTH: 0.564396
G1 F6903.482
G1 X111.747 Y119.57 E.00304
; LINE_WIDTH: 0.524068
G1 F7482.105
G1 X111.814 Y119.594 E.00281
; LINE_WIDTH: 0.48374
G1 F8166.598
G1 X111.882 Y119.619 E.00257
; LINE_WIDTH: 0.443412
G1 F8988.944
G1 X111.949 Y119.644 E.00234
; LINE_WIDTH: 0.383229
G1 F10578.641
G1 X112.016 Y119.668 E.00199
G1 X116.628 Y119.668 E.1279
M204 S10000
G1 X111.666 Y114.99 F42000
; LINE_WIDTH: 0.53879
G1 F7259.967
M204 S6000
G1 X111.717 Y114.912 E.00375
; LINE_WIDTH: 0.50137
G1 F7852.546
G1 X111.768 Y114.834 E.00347
; LINE_WIDTH: 0.466993
G1 F8489.114
G1 X111.892 Y114.772 E.00481
; LINE_WIDTH: 0.420066
G1 F9545.377
G1 X112.016 Y114.709 E.00427
G1 X112.72 Y114.709 E.02164
G2 X112.732 Y111.896 I-69.767 J-1.69 E.08645
G1 X112.8 Y111.728 E.00557
G2 X114.292 Y110.583 I-5.091 J-8.179 E.05791
G2 X116.227 Y106.743 I-4.837 J-4.845 E.1344
G1 X116.377 Y106.563 E.00724
G1 X116.616 Y106.517 E.00747
G1 X116.165 Y103.372 E.09764
G1 X113.086 Y103.372 E.09464
G1 X113.427 Y103.986 E.02158
G3 X113.638 Y106.915 I-4.095 J1.767 E.09196
G1 X113.397 Y107.581 E.02178
G3 X111.597 Y109.512 I-4.009 J-1.932 E.08235
G1 X111.597 Y114.29 E.14684
; LINE_WIDTH: 0.435658
G1 F9166.428
G1 X111.613 Y114.533 E.0078
; LINE_WIDTH: 0.466993
G1 F8489.114
G1 X111.629 Y114.777 E.00843
; LINE_WIDTH: 0.50137
G1 F7852.546
G1 X111.642 Y114.854 E.00292
; LINE_WIDTH: 0.53879
G1 F7259.967
G1 X111.656 Y114.931 E.00316
M204 S10000
G1 X111.975 Y114.348 F42000
; LINE_WIDTH: 0.420311
G1 F9539.199
M204 S6000
G1 X112.354 Y114.331 E.01165
G1 X112.354 Y111.896 E.07488
G1 X112.473 Y111.539 E.01157
G1 X112.681 Y111.332 E.00902
G1 X113.356 Y110.887 E.02486
G1 X113.991 Y110.346 E.02567
G2 X115.812 Y106.885 I-4.574 J-4.616 E.12215
G1 X115.951 Y106.453 E.01398
G1 X116.132 Y106.276 E.00778
G1 X116.197 Y106.252 E.00212
G1 X115.838 Y103.75 E.07775
G1 X113.728 Y103.75 E.06488
G1 X113.993 Y104.438 E.02268
G1 X114.134 Y105.094 E.02064
G3 X114.005 Y106.999 I-5.216 J.606 E.05904
G1 X113.748 Y107.717 E.02345
G1 X113.431 Y108.294 E.02024
G1 X113.104 Y108.732 E.01682
G1 X112.545 Y109.314 E.02483
G1 X112.007 Y109.715 E.02064
G1 X111.974 Y109.778 E.00218
G2 X111.975 Y111.896 I582.432 J.853 E.06513
G1 X111.975 Y114.288 E.07355
M204 S10000
G1 X112.352 Y111.146 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X112.493 Y111.005 E.00614
G1 X113.135 Y110.582 E.02363
G1 X113.739 Y110.065 E.02442
G2 X114.867 Y108.531 I-4.833 J-4.733 E.05869
G2 X115.443 Y106.809 I-5.849 J-2.913 E.05599
G1 X115.488 Y106.59 E.00686
G1 X115.645 Y106.233 E.01197
G1 X115.791 Y106.074 E.00664
G1 X115.511 Y104.127 E.06045
G1 X114.281 Y104.127 E.03779
G3 X114.555 Y105.728 I-5.043 J1.686 E.0501
G1 X114.506 Y106.449 E.02222
G3 X112.352 Y109.93 I-5.08 J-.737 E.12939
G1 X112.352 Y111.086 E.03552
M204 S10000
G1 X112.693 Y110.48 F42000
; LINE_WIDTH: 0.348906
G1 F11765.253
M204 S6000
G2 X115.11 Y106.739 I-3.177 J-4.704 E.11411
; LINE_WIDTH: 0.362357
G1 F11269.841
G1 X115.178 Y106.5 E.00647
; LINE_WIDTH: 0.39719
G1 F10161.741
G1 X115.246 Y106.261 E.00717
; LINE_WIDTH: 0.429556
G1 F9311.1
G1 X115.314 Y106.022 E.00783
G1 X115.373 Y105.948 E.00299
G2 X115.183 Y104.506 I-27.628 J2.915 E.04586
G1 X114.784 Y104.506 E.01256
G3 X114.944 Y105.89 I-7.538 J1.572 E.04398
; LINE_WIDTH: 0.4249
G1 F9424.577
G1 X114.896 Y106.183 E.00924
; LINE_WIDTH: 0.37582
G1 F10814.059
G1 X114.848 Y106.476 E.00806
; LINE_WIDTH: 0.349958
G1 F11724.937
G3 X112.693 Y110.103 I-5.418 J-.765 E.10836
G1 X112.693 Y110.42 E.00792
; WIPE_START
G1 X112.693 Y110.103 E-.12028
G1 X112.907 Y109.946 E-.1009
G1 X113.299 Y109.584 E-.20284
G1 X113.677 Y109.168 E-.21343
G1 X113.866 Y108.908 E-.12256
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.595 Y109.004 Z3.4 F42000
G1 Z3
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.241924
G1 F15000
M204 S6000
G1 X110.392 Y109.039 E.00334
; LINE_WIDTH: 0.20096
G1 X110.155 Y109.063 E.00306
; LINE_WIDTH: 0.152225
G1 X109.913 Y109.088 E.00217
; LINE_WIDTH: 0.117033
G1 X109.443 Y109.102 E.00284
G3 X108.952 Y109.082 I.03 J-6.751 E.00297
; LINE_WIDTH: 0.158209
G1 X108.794 Y109.064 E.00149
; LINE_WIDTH: 0.193946
G1 X108.637 Y109.046 E.00195
; LINE_WIDTH: 0.231409
G1 X108.464 Y109.026 E.00267
; LINE_WIDTH: 0.274088
G1 X108.346 Y109.004 E.00227
; LINE_WIDTH: 0.318302
G1 F13072.775
G1 X108.227 Y108.982 E.00271
; LINE_WIDTH: 0.362516
G1 F11264.229
G1 X108.108 Y108.959 E.00314
; LINE_WIDTH: 0.414201
G1 F9696.176
G1 X107.982 Y108.936 E.0039
G1 X107.854 Y108.655 E.00932
; WIPE_START
G1 X107.982 Y108.936 E-.5358
G1 X108.108 Y108.959 E-.2242
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X106.917 Y103.01 Z3.4 F42000
G1 Z3
G1 E.8 F1800
; LINE_WIDTH: 0.117197
G1 F15000
M204 S6000
G1 X107.137 Y102.777 E.00194
M204 S10000
G1 X107.797 Y102.603 F42000
; LINE_WIDTH: 0.399731
G1 F10089.383
M204 S6000
G1 X108.07 Y102.545 E.00811
; LINE_WIDTH: 0.373638
G1 F10885.409
G1 X108.188 Y102.525 E.00324
; LINE_WIDTH: 0.332274
G1 F12441.516
G1 X108.307 Y102.504 E.00284
; LINE_WIDTH: 0.29091
G1 F14516.736
G1 X108.425 Y102.483 E.00243
; LINE_WIDTH: 0.249546
G1 F15000
G1 X108.544 Y102.463 E.00203
; LINE_WIDTH: 0.227046
G1 X108.557 Y102.461 E.0002
; LINE_WIDTH: 0.201615
G1 X108.789 Y102.437 E.00302
; LINE_WIDTH: 0.154364
G1 X109.022 Y102.414 E.00212
; LINE_WIDTH: 0.117054
G3 X109.513 Y102.398 I.474 J7.217 E.00297
G1 X109.99 Y102.418 E.00289
; LINE_WIDTH: 0.157227
G1 X110.155 Y102.436 E.00155
; LINE_WIDTH: 0.193828
G1 X110.313 Y102.454 E.00196
; LINE_WIDTH: 0.22966
G1 X110.471 Y102.472 E.00242
; LINE_WIDTH: 0.270993
G1 X110.602 Y102.496 E.00247
; LINE_WIDTH: 0.316996
G1 F13135.079
G1 X110.718 Y102.518 E.00264
; LINE_WIDTH: 0.360326
G1 F11341.962
G1 X110.835 Y102.539 E.00306
; LINE_WIDTH: 0.403656
G1 F9979.61
G1 X110.951 Y102.561 E.00348
; LINE_WIDTH: 0.425056
G1 F9420.749
G1 X110.968 Y102.564 E.00054
G1 X111.094 Y102.85 E.00972
; WIPE_START
G1 X110.968 Y102.564 E-.72024
G1 X110.951 Y102.561 E-.03976
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X103.344 Y103.187 Z3.4 F42000
G1 X101.089 Y103.372 Z3.4
G1 Z3
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X101.406 Y103.94 E.01997
G3 X101.632 Y106.957 I-4.111 J1.824 E.0948
G3 X101.089 Y108.128 I-4.07 J-1.174 E.03981
G1 X105.864 Y108.128 E.14673
G1 X105.529 Y107.526 E.02115
G3 X105.186 Y105.225 I3.886 J-1.755 E.07243
G1 X105.333 Y104.495 E.02285
G3 X105.851 Y103.377 I4.42 J1.367 E.038
G2 X101.149 Y103.372 I-2.654 J339.58 E.14447
M204 S10000
G1 X101.732 Y103.749 F42000
G1 F9547.299
M204 S6000
G1 X101.977 Y104.386 E.02096
G1 X102.126 Y105.041 E.02062
G3 X102 Y107.037 I-5.389 J.663 E.06181
G2 X101.743 Y107.751 I15.096 J5.84 E.02331
G1 X105.221 Y107.751 E.10687
G1 X104.958 Y107.062 E.02264
G1 X104.816 Y106.406 E.02064
G3 X104.965 Y104.411 I5.448 J-.597 E.0618
G1 X105.218 Y103.75 E.02176
G1 X101.792 Y103.749 E.10527
M204 S10000
G1 X102.283 Y104.127 F42000
G1 F9547.299
M204 S6000
G1 X102.494 Y104.96 E.02643
G3 X102.368 Y107.117 I-5.789 J.745 E.06676
G1 X102.283 Y107.373 E.00831
G1 X104.669 Y107.373 E.07332
G3 X104.435 Y105.164 I4.641 J-1.61 E.06885
G1 X104.598 Y104.327 E.02622
G1 X104.665 Y104.127 E.00648
G1 X102.343 Y104.127 E.07133
M204 S10000
G1 X102.781 Y104.504 F42000
G1 F9547.299
M204 S6000
G3 X102.781 Y106.996 I-5.116 J1.246 E.07733
G1 X104.168 Y106.996 E.04263
G3 X104.17 Y104.504 I5.245 J-1.242 E.07729
G1 X102.841 Y104.504 E.04085
M204 S10000
G1 X103.253 Y104.89 F42000
; LINE_WIDTH: 0.424474
G1 F9435.112
M204 S6000
G3 X103.252 Y106.611 I-9.956 J.851 E.05359
G1 X103.698 Y106.611 E.01387
G3 X103.697 Y104.89 I10.21 J-.864 E.05359
G1 X103.313 Y104.89 E.01193
; WIPE_START
G1 X103.697 Y104.89 E-.14586
G1 X103.674 Y105.104 E-.08164
G1 X103.655 Y105.872 E-.29223
G1 X103.691 Y106.504 E-.24026
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X100.065 Y103.04 Z3.4 F42000
G1 Z3
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.108304
G1 F15000
M204 S6000
G1 X99.942 Y102.899 E.001
; LINE_WIDTH: 0.134114
G1 X99.82 Y102.777 E.00128
M204 S10000
G1 X99.154 Y102.613 F42000
; LINE_WIDTH: 0.426399
G1 F9387.748
M204 S6000
G2 X98.92 Y102.554 I-.941 J3.251 E.00756
; LINE_WIDTH: 0.389839
G1 F10377.067
G1 X98.801 Y102.533 E.0034
; LINE_WIDTH: 0.34708
G1 F11835.907
G1 X98.683 Y102.511 E.00298
; LINE_WIDTH: 0.30432
G1 F13772.023
G1 X98.565 Y102.49 E.00256
; LINE_WIDTH: 0.259112
G1 F15000
G1 X98.432 Y102.466 E.00237
; LINE_WIDTH: 0.219178
G1 X98.274 Y102.449 E.00228
; LINE_WIDTH: 0.185179
G1 X98.116 Y102.432 E.00184
; LINE_WIDTH: 0.150494
G1 X97.951 Y102.415 E.00145
; LINE_WIDTH: 0.116356
G1 X97.473 Y102.398 E.00286
G2 X96.992 Y102.415 I-.003 J6.559 E.00288
; LINE_WIDTH: 0.151175
G1 X96.834 Y102.432 E.0014
; LINE_WIDTH: 0.185153
G1 X96.676 Y102.449 E.00184
; LINE_WIDTH: 0.220675
G1 X96.504 Y102.468 E.00251
; LINE_WIDTH: 0.261526
G1 X96.386 Y102.49 E.00215
; LINE_WIDTH: 0.304307
G1 F13772.698
G1 X96.267 Y102.511 E.00257
; LINE_WIDTH: 0.347088
G1 F11835.565
G1 X96.148 Y102.533 E.00299
; LINE_WIDTH: 0.38987
G1 F10376.154
G1 X96.03 Y102.554 E.00341
; LINE_WIDTH: 0.426424
G1 F9387.143
G2 X95.796 Y102.613 I.711 J3.326 E.00755
M204 S10000
G1 X94.732 Y103.839 F42000
; LINE_WIDTH: 0.106649
G1 F15000
M204 S6000
G1 X94.649 Y103.937 E.00067
G2 X94.615 Y104.027 I.093 J.086 E.00052
M204 S10000
G1 X94.448 Y104.756 F42000
; LINE_WIDTH: 0.497432
G1 F7920.587
M204 S6000
G1 X94.419 Y105.024 E.00999
; LINE_WIDTH: 0.463229
G1 F8565.134
G2 X94.389 Y105.321 I4.134 J.58 E.01023
; LINE_WIDTH: 0.429919
G1 F9302.353
G2 X94.391 Y106.208 I8.942 J.423 E.028
; LINE_WIDTH: 0.465008
G1 F8529.039
G1 X94.419 Y106.476 E.00927
; LINE_WIDTH: 0.49743
G1 F7920.633
G1 X94.448 Y106.744 E.00999
M204 S10000
G1 X94.615 Y107.473 F42000
; LINE_WIDTH: 0.106644
G1 F15000
M204 S6000
G2 X94.649 Y107.564 I.126 J.005 E.00052
G1 X94.732 Y107.661 E.00067
M204 S10000
G1 X95.796 Y108.887 F42000
; LINE_WIDTH: 0.426431
G1 F9386.966
M204 S6000
G2 X96.03 Y108.946 I.949 J-3.282 E.00755
; LINE_WIDTH: 0.389913
G1 F10374.848
G1 X96.148 Y108.967 E.00341
; LINE_WIDTH: 0.347138
G1 F11833.623
G1 X96.267 Y108.989 E.00299
; LINE_WIDTH: 0.304363
G1 F13769.746
G1 X96.385 Y109.01 E.00257
; LINE_WIDTH: 0.261588
G1 F15000
G1 X96.504 Y109.032 E.00215
; LINE_WIDTH: 0.220742
G1 X96.676 Y109.051 E.00251
; LINE_WIDTH: 0.185198
G1 X96.834 Y109.068 E.00184
; LINE_WIDTH: 0.1512
G1 X96.992 Y109.085 E.0014
; LINE_WIDTH: 0.116376
G2 X97.473 Y109.102 I.477 J-6.538 E.00288
G1 X97.951 Y109.085 E.00286
; LINE_WIDTH: 0.150516
G1 X98.116 Y109.068 E.00145
; LINE_WIDTH: 0.185193
G1 X98.274 Y109.051 E.00184
; LINE_WIDTH: 0.219185
G1 X98.432 Y109.034 E.00228
; LINE_WIDTH: 0.259129
G1 X98.564 Y109.01 E.00237
; LINE_WIDTH: 0.304342
G1 F13770.848
G1 X98.683 Y108.989 E.00257
; LINE_WIDTH: 0.347109
G1 F11834.744
G1 X98.802 Y108.967 E.00299
; LINE_WIDTH: 0.389877
G1 F10375.943
G1 X98.92 Y108.946 E.00341
; LINE_WIDTH: 0.426424
G1 F9387.132
G2 X99.154 Y108.887 I-.722 J-3.375 E.00755
M204 S10000
G1 X99.82 Y108.723 F42000
; LINE_WIDTH: 0.133941
G1 F15000
M204 S6000
G1 X99.942 Y108.601 E.00128
; LINE_WIDTH: 0.1082
G1 X100.064 Y108.461 E.00099
; WIPE_START
G1 X99.942 Y108.601 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.064 Y111.346 Z3.4 F42000
G1 X116.695 Y115.057 Z3.4
G1 Z3
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.695 Y116.685 E.05401
G1 X116.206 Y116.355 E.01957
G2 X114.634 Y115.704 I-1.319 J.962 E.05938
G1 X114.11 Y116.058 E.02099
G3 X113.062 Y116.738 I-1.371 J-.965 E.04248
G3 X112.127 Y116.432 I-.21 J-.936 E.03427
G1 X112.127 Y118.259 E.06062
G2 X113.586 Y118.806 I1.198 J-.977 E.05416
G1 X114.11 Y118.451 E.02099
G3 X115.682 Y117.8 I1.319 J.962 E.05938
G3 X116.695 Y118.604 I-2.169 J3.773 E.04305
G1 X116.695 Y119.244 E.02124
G1 X116.592 Y119.317 E.00417
G1 X115.742 Y119.317 E.02819
; CHANGE_LAYER
; Z_HEIGHT: 3.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8843.478
G1 X116.592 Y119.317 E-.32293
G1 X116.695 Y119.244 E-.04772
G1 X116.695 Y118.604 E-.24333
G1 X116.412 Y118.344 E-.14603
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 16/79
; update layer progress
M73 L16
M991 S0 P15 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z3.4 I.675 J-1.012 P1  F42000
G1 X99.082 Y106.783 Z3.4
G1 Z3.2
G1 E.8 F1800
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X98.92 Y106.987 E.00799
G3 X97.203 Y103.859 I-1.451 J-1.238 E.22666
G1 X97.463 Y103.84 E.00801
G3 X99.102 Y106.735 I.006 J1.908 E.12411
; WIPE_START
M204 S6000
G1 X98.92 Y106.987 E-.11806
G1 X98.727 Y107.194 E-.10763
G1 X98.508 Y107.357 E-.10382
G1 X98.269 Y107.488 E-.1036
G1 X98.013 Y107.583 E-.10356
G1 X97.747 Y107.641 E-.10359
G1 X97.475 Y107.661 E-.10359
G1 X97.433 Y107.658 E-.01614
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X105.065 Y107.575 Z3.6 F42000
G1 X110.186 Y107.52 Z3.6
G1 Z3.2
G1 E.8 F1800
G1 F3600
M204 S5000
G1 X109.989 Y107.585 E.00638
G3 X109.238 Y103.855 I-.51 J-1.838 E.19256
G1 X109.499 Y103.84 E.00802
G3 X110.241 Y107.496 I-.019 J1.907 E.15948
; WIPE_START
M204 S6000
G1 X109.989 Y107.585 E-.1016
G1 X109.723 Y107.644 E-.10366
G1 X109.44 Y107.66 E-.10773
G1 X109.18 Y107.638 E-.09923
G1 X108.914 Y107.576 E-.10357
G1 X108.659 Y107.478 E-.10381
G1 X108.413 Y107.337 E-.10783
G1 X108.345 Y107.285 E-.03257
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X109.846 Y99.802 Z3.6 F42000
G1 X116.734 Y65.452 Z3.6
G1 Z3.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.716 Y65.452 E.03257
G1 X117.716 Y98.048 E1.08128
G1 X116.734 Y98.048 E.03257
G1 X116.734 Y65.512 E1.07929
; WIPE_START
G1 X117.716 Y65.452 E-.37375
G1 X117.716 Y66.468 E-.38625
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.43 Y74.095 Z3.6 F42000
G1 X116.214 Y106.482 Z3.6
G1 Z3.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X117.007 Y106.482 E.0263
G1 X117.081 Y106.998 E.01729
G1 X117.081 Y120.02 E.43196
G1 X111.205 Y120.02 E.19491
G1 X111.205 Y114.673 E.17735
G1 X112.696 Y114.673 E.04945
G1 X112.696 Y111.717 E.09805
G2 X116.208 Y106.541 I-3.164 J-5.926 E.21582
M204 S10000
G1 X115.847 Y106.075 F42000
G1 F8843.478
M204 S6000
G1 X117.36 Y106.075 E.05018
G1 X117.488 Y106.969 E.02996
G1 X117.488 Y120.181 E.43826
G1 X117.407 Y120.427 E.0086
G1 X110.798 Y120.427 E.21922
G1 X110.798 Y114.266 E.20436
G1 X112.289 Y114.266 E.04945
G1 X112.289 Y111.472 E.09267
G1 X112.359 Y111.442 E.00253
G2 X115.844 Y106.135 I-2.885 J-5.693 E.22043
M204 S10000
G1 X115.439 Y105.668 F42000
G1 F8843.478
M204 S6000
G1 X117.713 Y105.668 E.07542
G1 X117.895 Y106.94 E.04263
G1 X117.895 Y120.246 E.44139
G1 X117.701 Y120.834 E.02053
G1 X110.391 Y120.834 E.24249
G1 X110.391 Y113.859 E.23137
G1 X111.882 Y113.859 E.04945
G1 X111.882 Y111.207 E.08796
G2 X115.44 Y105.728 I-2.364 J-5.43 E.22957
M204 S10000
G1 X115.012 Y105.261 F42000
G1 F8843.478
M204 S6000
G1 X118.066 Y105.261 E.1013
G1 X118.302 Y106.911 E.0553
G1 X118.302 Y120.311 E.44453
G1 X117.995 Y121.241 E.03247
G1 X109.984 Y121.241 E.26575
G1 X109.984 Y113.452 E.25837
G1 X111.475 Y113.452 E.04945
G1 X111.475 Y110.942 E.08326
G2 X115.017 Y105.32 I-2.017 J-5.198 E.23612
; WIPE_START
G1 X117.017 Y105.281 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.15 Y97.65 Z3.6 F42000
G1 X117.78 Y61.805 Z3.6
G1 Z3.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X118.123 Y61.805 E.01138
G1 X118.123 Y102.793 E1.35966
G1 X118.709 Y106.882 E.13702
G1 X118.709 Y120.377 E.44766
G1 X118.29 Y121.648 E.0444
G1 X109.577 Y121.648 E.28902
G1 X109.577 Y113.045 E.28538
G1 X111.068 Y113.045 E.04945
G1 X111.068 Y110.648 E.07951
G2 X114.559 Y104.854 I-1.598 J-4.912 E.24466
G1 X117.78 Y104.854 E.10685
G1 X117.78 Y98.455 E.21225
G1 X116.327 Y98.455 E.04819
G1 X116.327 Y65.045 E1.10828
G1 X117.78 Y65.045 E.04819
G1 X117.78 Y61.865 E.10549
; WIPE_START
G1 X118.123 Y61.805 E-.13239
G1 X118.123 Y63.456 E-.62761
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.495 Y63.721 Z3.6 F42000
G1 X60.534 Y65.452 Z3.6
G1 Z3.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X61.516 Y65.452 E.03257
G1 X61.516 Y93.741 E.9384
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y65.512 E.93641
; WIPE_START
G1 X61.516 Y65.452 E-.37375
G1 X61.516 Y66.468 E-.38625
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X60.47 Y60.695 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
G1 F8843.478
M204 S6000
G1 X60.47 Y65.045 E.14428
G1 X61.923 Y65.045 E.04819
G1 X61.923 Y94.148 E.9654
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X60.47 Y58.352 E.01138
G1 X60.47 Y60.635 E.07574
; WIPE_START
G1 X60.47 Y62.635 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X62.315 Y62.54 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E.98327
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X118.515 Y57.96 E1.80615
G1 X118.515 Y102.765 E1.37673
G1 X119.101 Y106.854 E.12692
G1 X119.101 Y120.44 E.41747
G1 X118.573 Y122.04 E.05178
G1 X109.185 Y122.04 E.28847
G1 X109.185 Y110.54 E.35336
G1 X93.185 Y110.54 E.49164
G1 X93.185 Y100.96 E.29437
G1 X115.935 Y100.96 E.69904
G1 X115.935 Y62.54 E1.18054
G1 X62.375 Y62.54 E1.64575
; WIPE_START
M204 S6000
G1 X62.371 Y64.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z3.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z3.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z3.6 F4000
            G39.3 S1
            G0 Z3.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y65.655 F42000
G1 Z3.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.30564
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.61 Y92.389 Z3.6 F42000
G1 X117.225 Y97.845 Z3.6
M73 P59 R10
G1 Z3.2
G1 E.8 F1800
G1 F6264.574
M204 S6000
G1 X117.225 Y65.655 E1.50734
; WIPE_START
G1 X117.225 Y67.655 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X118.308 Y60.892 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; FEATURE: Top surface
; LINE_WIDTH: 0.42
G1 F9547.055
M204 S2000
G1 X117.618 Y61.582 E.02998
M204 S10000
G1 X117.557 Y64.309 F42000
G1 F9547.055
M204 S2000
G1 X117.044 Y64.822 E.0223
G1 X116.511 Y64.822
G1 X117.557 Y63.776 E.04548
G1 X117.557 Y63.243
G1 X116.142 Y64.657 E.06148
G1 X116.142 Y64.124
G1 X117.557 Y62.709 E.06148
G1 X117.557 Y62.176
G1 X116.142 Y63.591 E.06148
G1 X116.142 Y63.058
G1 X117.557 Y61.643 E.06148
M204 S10000
G1 X116.142 Y62.524 F42000
G1 F9547.055
M204 S2000
G1 X118.308 Y60.359 E.09409
G1 X118.308 Y59.826
G1 X115.801 Y62.333 E.10893
G1 X115.268 Y62.333
G1 X118.308 Y59.293 E.1321
G1 X118.308 Y58.759
G1 X114.734 Y62.333 E.15527
G1 X114.201 Y62.333
G1 X118.308 Y58.226 E.17845
G1 X117.833 Y58.167
G1 X113.668 Y62.333 E.181
G1 X113.135 Y62.333
G1 X117.3 Y58.167 E.181
G1 X116.767 Y58.167
G1 X112.601 Y62.333 E.181
G1 X112.068 Y62.333
G1 X116.233 Y58.167 E.181
G1 X115.7 Y58.167
G1 X111.535 Y62.333 E.181
G1 X111.002 Y62.333
G1 X115.167 Y58.167 E.181
G1 X114.634 Y58.167
G1 X110.468 Y62.333 E.181
G1 X109.935 Y62.333
G1 X114.1 Y58.167 E.181
G1 X113.567 Y58.167
G1 X109.402 Y62.333 E.181
G1 X108.869 Y62.333
G1 X113.034 Y58.167 E.181
G1 X112.501 Y58.167
G1 X108.335 Y62.333 E.181
G1 X107.802 Y62.333
G1 X111.967 Y58.167 E.181
G1 X111.434 Y58.167
G1 X107.269 Y62.333 E.181
G1 X106.736 Y62.333
G1 X110.901 Y58.167 E.181
G1 X110.368 Y58.167
G1 X106.202 Y62.333 E.181
G1 X105.669 Y62.333
G1 X109.834 Y58.167 E.181
G1 X109.301 Y58.167
G1 X105.136 Y62.333 E.181
G1 X104.603 Y62.333
G1 X108.768 Y58.167 E.181
G1 X108.234 Y58.167
G1 X104.069 Y62.333 E.181
G1 X103.536 Y62.333
G1 X107.701 Y58.167 E.181
G1 X107.168 Y58.167
G1 X103.003 Y62.333 E.181
G1 X102.469 Y62.333
G1 X106.635 Y58.167 E.181
G1 X106.101 Y58.167
G1 X101.936 Y62.333 E.181
G1 X101.403 Y62.333
G1 X105.568 Y58.167 E.181
G1 X105.035 Y58.167
G1 X100.87 Y62.333 E.181
G1 X100.336 Y62.333
G1 X104.502 Y58.167 E.181
G1 X103.968 Y58.167
G1 X99.803 Y62.333 E.181
G1 X99.27 Y62.333
G1 X103.435 Y58.167 E.181
G1 X102.902 Y58.167
G1 X98.737 Y62.333 E.181
G1 X98.203 Y62.333
G1 X102.369 Y58.167 E.181
G1 X101.835 Y58.167
G1 X97.67 Y62.333 E.181
G1 X97.137 Y62.333
G1 X101.302 Y58.167 E.181
G1 X100.769 Y58.167
G1 X96.604 Y62.333 E.181
G1 X96.07 Y62.333
G1 X100.236 Y58.167 E.181
G1 X99.702 Y58.167
G1 X95.537 Y62.333 E.181
G1 X95.004 Y62.333
G1 X99.169 Y58.167 E.181
G1 X98.636 Y58.167
M73 P59 R9
G1 X94.471 Y62.333 E.181
G1 X93.937 Y62.333
G1 X98.103 Y58.167 E.181
G1 X97.569 Y58.167
G1 X93.404 Y62.333 E.181
G1 X92.871 Y62.333
G1 X97.036 Y58.167 E.181
G1 X96.503 Y58.167
G1 X92.338 Y62.333 E.181
G1 X91.804 Y62.333
G1 X95.97 Y58.167 E.181
G1 X95.436 Y58.167
G1 X91.271 Y62.333 E.181
G1 X90.738 Y62.333
G1 X94.903 Y58.167 E.181
G1 X94.37 Y58.167
G1 X90.205 Y62.333 E.181
G1 X89.671 Y62.333
G1 X93.837 Y58.167 E.181
G1 X93.303 Y58.167
G1 X89.138 Y62.333 E.181
G1 X88.605 Y62.333
G1 X92.77 Y58.167 E.181
G1 X92.237 Y58.167
G1 X88.072 Y62.333 E.181
G1 X87.538 Y62.333
G1 X91.704 Y58.167 E.181
G1 X91.17 Y58.167
G1 X87.005 Y62.333 E.181
G1 X86.472 Y62.333
G1 X90.637 Y58.167 E.181
G1 X90.104 Y58.167
G1 X85.938 Y62.333 E.181
G1 X85.405 Y62.333
G1 X89.57 Y58.167 E.181
G1 X89.037 Y58.167
G1 X84.872 Y62.333 E.181
G1 X84.339 Y62.333
G1 X88.504 Y58.167 E.181
G1 X87.971 Y58.167
G1 X83.805 Y62.333 E.181
G1 X83.272 Y62.333
G1 X87.437 Y58.167 E.181
G1 X86.904 Y58.167
G1 X82.739 Y62.333 E.181
G1 X82.206 Y62.333
G1 X86.371 Y58.167 E.181
G1 X85.838 Y58.167
G1 X81.672 Y62.333 E.181
G1 X81.139 Y62.333
G1 X85.304 Y58.167 E.181
G1 X84.771 Y58.167
G1 X80.606 Y62.333 E.181
M73 P60 R9
G1 X80.073 Y62.333
G1 X84.238 Y58.167 E.181
G1 X83.705 Y58.167
G1 X79.539 Y62.333 E.181
G1 X79.006 Y62.333
G1 X83.171 Y58.167 E.181
G1 X82.638 Y58.167
G1 X78.473 Y62.333 E.181
G1 X77.94 Y62.333
G1 X82.105 Y58.167 E.181
G1 X81.572 Y58.167
G1 X77.406 Y62.333 E.181
G1 X76.873 Y62.333
G1 X81.038 Y58.167 E.181
G1 X80.505 Y58.167
G1 X76.34 Y62.333 E.181
G1 X75.807 Y62.333
G1 X79.972 Y58.167 E.181
G1 X79.439 Y58.167
G1 X75.273 Y62.333 E.181
G1 X74.74 Y62.333
G1 X78.905 Y58.167 E.181
G1 X78.372 Y58.167
G1 X74.207 Y62.333 E.181
G1 X73.674 Y62.333
G1 X77.839 Y58.167 E.181
G1 X77.306 Y58.167
G1 X73.14 Y62.333 E.181
G1 X72.607 Y62.333
G1 X76.772 Y58.167 E.181
G1 X76.239 Y58.167
G1 X72.074 Y62.333 E.181
G1 X71.541 Y62.333
G1 X75.706 Y58.167 E.181
G1 X75.173 Y58.167
G1 X71.007 Y62.333 E.181
G1 X70.474 Y62.333
G1 X74.639 Y58.167 E.181
G1 X74.106 Y58.167
G1 X69.941 Y62.333 E.181
G1 X69.408 Y62.333
G1 X73.573 Y58.167 E.181
G1 X73.039 Y58.167
G1 X68.874 Y62.333 E.181
G1 X68.341 Y62.333
G1 X72.506 Y58.167 E.181
G1 X71.973 Y58.167
G1 X67.808 Y62.333 E.181
G1 X67.274 Y62.333
G1 X71.44 Y58.167 E.181
G1 X70.906 Y58.167
G1 X66.741 Y62.333 E.181
G1 X66.208 Y62.333
G1 X70.373 Y58.167 E.181
G1 X69.84 Y58.167
G1 X65.675 Y62.333 E.181
G1 X65.141 Y62.333
G1 X69.307 Y58.167 E.181
G1 X68.773 Y58.167
G1 X64.608 Y62.333 E.181
G1 X64.075 Y62.333
G1 X68.24 Y58.167 E.181
G1 X67.707 Y58.167
G1 X63.542 Y62.333 E.181
G1 X63.008 Y62.333
G1 X67.174 Y58.167 E.181
G1 X66.64 Y58.167
G1 X62.475 Y62.333 E.181
; WIPE_START
M204 S6000
G1 X63.889 Y60.918 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X62.108 Y64.3 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
G1 F9547.055
M204 S2000
G1 X61.585 Y64.822 E.0227
G1 X61.052 Y64.822
G1 X62.108 Y63.767 E.04587
G1 X62.108 Y63.233
G1 X60.693 Y64.648 E.06148
G1 X60.693 Y64.115
G1 X62.108 Y62.7 E.06148
M204 S10000
G1 X60.693 Y63.582 F42000
G1 F9547.055
M204 S2000
G1 X66.107 Y58.167 E.23528
G1 X65.574 Y58.167
G1 X60.693 Y63.049 E.21211
G1 X60.693 Y62.515
G1 X65.041 Y58.167 E.18894
G1 X64.507 Y58.167
G1 X60.693 Y61.982 E.16576
G1 X60.693 Y61.449
G1 X63.974 Y58.167 E.14259
G1 X63.441 Y58.167
G1 X60.693 Y60.915 E.11942
G1 X60.693 Y60.382
G1 X62.908 Y58.167 E.09625
G1 X62.374 Y58.167
G1 X60.693 Y59.849 E.07307
G1 X60.693 Y59.316
G1 X61.841 Y58.167 E.0499
G1 X61.308 Y58.167
G1 X60.693 Y58.782 E.02673
M204 S10000
G1 X61.036 Y64.806 F42000
; FEATURE: Gap infill
; LINE_WIDTH: 0.112651
G1 F15000
M204 S6000
G1 X60.674 Y64.806 E.00206
; WIPE_START
G1 X61.036 Y64.806 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.668 Y64.807 Z3.6 F42000
G1 X116.5 Y64.812 Z3.6
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.101931
G1 F15000
M204 S6000
G1 X116.124 Y64.812 E.00181
; WIPE_START
G1 X116.5 Y64.812 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.797 Y72.438 Z3.6 F42000
G1 X118.008 Y103.604 Z3.6
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.120219
G1 F15000
M204 S6000
G1 X118.034 Y103.967 E.00229
; LINE_WIDTH: 0.166802
G1 X118.06 Y104.331 E.00368
; LINE_WIDTH: 0.213385
G1 X118.086 Y104.694 E.00506
; LINE_WIDTH: 0.259969
G1 X118.112 Y105.057 E.00644
; WIPE_START
G1 X118.086 Y104.694 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.696 Y104.631 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; FEATURE: Top surface
; LINE_WIDTH: 0.42
G1 F9547.055
M204 S2000
G1 X117.557 Y103.77 E.03741
G1 X117.557 Y103.237
G1 X116.163 Y104.631 E.06058
G1 X115.63 Y104.631
G1 X117.557 Y102.704 E.08376
G1 X117.557 Y102.17
G1 X115.097 Y104.631 E.10693
G1 X114.563 Y104.631
G1 X117.557 Y101.637 E.1301
; WIPE_START
M204 S6000
G1 X116.143 Y103.051 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.873 Y107.987 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
G1 F9547.055
M204 S2000
G1 X111.713 Y110.148 E.09387
; WIPE_START
M204 S6000
G1 X113.127 Y108.733 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.845 Y112.082 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
G1 F9547.055
M204 S2000
G1 X110.105 Y112.822 E.03218
G1 X109.572 Y112.822
G1 X110.845 Y111.549 E.05535
G1 X110.845 Y111.015
G1 X109.392 Y112.468 E.06313
G1 X109.392 Y111.935
G1 X114.213 Y107.114 E.20949
G1 X114.358 Y106.436
G1 X109.392 Y111.402 E.21579
G1 X109.392 Y110.868
G1 X114.403 Y105.858 E.21774
G1 X114.387 Y105.34
G1 X109.392 Y110.335 E.21706
G1 X108.862 Y110.333
G1 X114.326 Y104.868 E.23745
; WIPE_START
M204 S6000
G1 X112.912 Y106.282 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X108.328 Y110.333 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
G1 F9547.055
M204 S2000
G1 X117.557 Y101.104 E.40103
G1 X117.557 Y100.571
G1 X111.281 Y106.846 E.27271
G1 X111.573 Y106.022
G1 X117.557 Y100.037 E.26006
G1 X117.557 Y99.504
G1 X116.142 Y100.919 E.06148
G1 X116.142 Y100.386
G1 X117.557 Y98.971 E.06148
G1 X117.317 Y98.678
G1 X116.142 Y99.852 E.05105
G1 X116.142 Y99.319
G1 X116.784 Y98.678 E.02788
M204 S10000
G1 X115.894 Y101.167 F42000
G1 F9547.055
M204 S2000
G1 X111.576 Y105.485 E.18763
G1 X111.471 Y105.057
G1 X115.361 Y101.167 E.16901
G1 X114.827 Y101.167
G1 X111.305 Y104.69 E.15307
G1 X111.086 Y104.375
G1 X114.294 Y101.167 E.13941
G1 X113.761 Y101.167
G1 X110.814 Y104.114 E.12805
G1 X110.496 Y103.9
G1 X113.228 Y101.167 E.11872
G1 X112.694 Y101.167
G1 X110.126 Y103.736 E.11162
G1 X109.682 Y103.647
G1 X110.487 Y102.841 E.03502
G1 X110.549 Y102.78
G1 X112.161 Y101.167 E.07007
G1 X111.628 Y101.167
G1 X109.13 Y103.665 E.10853
G1 X108.191 Y104.071
G1 X111.095 Y101.167 E.12618
; WIPE_START
M204 S6000
G1 X109.68 Y102.582 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.563 Y107.565 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
G1 F9547.055
M204 S2000
G1 X107.795 Y110.333 E.12028
G1 X107.262 Y110.333
G1 X109.744 Y107.851 E.10784
G1 X109.213 Y107.849
G1 X106.729 Y110.333 E.10795
G1 X106.195 Y110.333
G1 X108.781 Y107.747 E.11235
G1 X108.417 Y107.578
G1 X105.662 Y110.333 E.1197
G1 X105.129 Y110.333
G1 X108.102 Y107.36 E.12919
G1 X107.838 Y107.091
G1 X104.596 Y110.333 E.14087
G1 X104.062 Y110.333
G1 X107.625 Y106.77 E.1548
G1 X107.463 Y106.399
G1 X103.529 Y110.333 E.17094
G1 X102.996 Y110.333
G1 X107.371 Y105.958 E.19011
G1 X107.385 Y105.41
G1 X102.463 Y110.333 E.21389
G1 X101.929 Y110.333
G1 X107.799 Y104.463 E.25508
; WIPE_START
M204 S6000
G1 X106.385 Y105.877 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X110.561 Y101.167 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
G1 F9547.055
M204 S2000
G1 X101.396 Y110.333 E.39827
G1 X100.863 Y110.333
G1 X110.028 Y101.167 E.39827
G1 X109.495 Y101.167
G1 X100.33 Y110.333 E.39827
G1 X99.796 Y110.333
G1 X108.962 Y101.167 E.39827
G1 X108.428 Y101.167
G1 X99.263 Y110.333 E.39827
G1 X98.73 Y110.333
G1 X107.895 Y101.167 E.39827
G1 X107.362 Y101.167
G1 X98.197 Y110.333 E.39827
G1 X97.663 Y110.333
G1 X106.829 Y101.167 E.39827
G1 X106.295 Y101.167
G1 X97.13 Y110.333 E.39827
G1 X96.597 Y110.333
G1 X105.762 Y101.167 E.39827
G1 X105.229 Y101.167
G1 X96.064 Y110.333 E.39827
G1 X95.53 Y110.333
G1 X98.085 Y107.778 E.11103
G1 X97.462 Y107.868
G1 X94.997 Y110.333 E.10712
G1 X94.464 Y110.333
G1 X96.99 Y107.807 E.10976
G1 X96.589 Y107.674
G1 X93.931 Y110.333 E.11553
G1 X93.397 Y110.333
G1 X96.254 Y107.476 E.12415
G1 X95.967 Y107.23
G1 X93.392 Y109.804 E.11188
G1 X93.392 Y109.271
G1 X95.725 Y106.938 E.10137
G1 X95.536 Y106.594
G1 X93.392 Y108.738 E.09315
G1 X93.392 Y108.204
G1 X95.408 Y106.189 E.08759
G1 X95.36 Y105.704
G1 X93.392 Y107.671 E.0855
G1 X93.392 Y107.138
G1 X95.481 Y105.049 E.09077
; WIPE_START
M204 S6000
G1 X94.067 Y106.463 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X99.503 Y106.36 Z3.6 F42000
M73 P61 R9
G1 Z3.2
G1 E.8 F1800
G1 F9547.055
M204 S2000
G1 X104.696 Y101.167 E.22566
G1 X104.162 Y101.167
G1 X99.593 Y105.737 E.19858
G1 X99.532 Y105.265
G1 X103.629 Y101.167 E.17804
G1 X103.096 Y101.167
G1 X99.399 Y104.864 E.16065
G1 X99.201 Y104.529
G1 X102.562 Y101.167 E.14609
G1 X102.029 Y101.167
G1 X98.955 Y104.242 E.13359
G1 X98.662 Y104.001
G1 X101.496 Y101.167 E.12313
G1 X100.963 Y101.167
G1 X98.32 Y103.81 E.11483
G1 X97.914 Y103.683
G1 X100.429 Y101.167 E.10931
G1 X99.896 Y101.167
G1 X97.429 Y103.635 E.10722
G1 X96.774 Y103.756
G1 X99.363 Y101.167 E.11249
G1 X98.83 Y101.167
G1 X93.392 Y106.605 E.23628
G1 X93.392 Y106.071
G1 X98.296 Y101.167 E.2131
G1 X97.763 Y101.167
G1 X93.392 Y105.538 E.18993
G1 X93.392 Y105.005
G1 X97.23 Y101.167 E.16676
G1 X96.697 Y101.167
G1 X93.392 Y104.472 E.14359
G1 X93.392 Y103.938
G1 X96.163 Y101.167 E.12041
G1 X95.63 Y101.167
G1 X93.392 Y103.405 E.09724
G1 X93.392 Y102.872
G1 X95.097 Y101.167 E.07407
G1 X94.564 Y101.167
G1 X93.392 Y102.339 E.0509
G1 X93.392 Y101.805
G1 X94.03 Y101.167 E.02772
; WIPE_START
M204 S6000
G1 X93.392 Y101.805 E-.34285
G1 X93.392 Y102.339 E-.20264
G1 X93.792 Y101.939 E-.21451
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X98.508 Y107.594 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.123309
G1 F15000
M204 S6000
G3 X98.155 Y107.847 I-3.786 J-4.912 E.00284
M204 S10000
G1 X97.227 Y107.836 F42000
; LINE_WIDTH: 0.0947971
G1 F15000
M204 S6000
G1 X97.07 Y107.888 E.0007
; WIPE_START
G1 X97.227 Y107.836 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X95.699 Y104.593 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.110511
G1 F15000
M204 S6000
G1 X95.6 Y104.725 E.00091
; LINE_WIDTH: 0.166757
G2 X95.415 Y104.983 I3.654 J2.82 E.0032
; WIPE_START
G1 X95.6 Y104.725 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X96.707 Y103.689 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.1739
G1 F15000
M204 S6000
G1 X96.572 Y103.783 E.00176
; LINE_WIDTH: 0.151204
G1 X96.445 Y103.879 E.0014
; LINE_WIDTH: 0.109185
G1 X96.317 Y103.974 E.00086
; WIPE_START
G1 X96.445 Y103.879 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X97.889 Y103.679 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.142806
G1 F15000
M204 S6000
G1 X97.781 Y103.621 E.00099
G1 X97.67 Y103.66 E.00095
; WIPE_START
G1 X97.781 Y103.621 E-.37168
G1 X97.889 Y103.679 E-.38832
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X99.572 Y106.429 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.123319
G1 F15000
M204 S6000
G3 X99.319 Y106.783 I-4.874 J-3.216 E.00284
; WIPE_START
G1 X99.572 Y106.429 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.204 Y106.364 Z3.6 F42000
G1 X107.451 Y106.362 Z3.6
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.0966356
G1 F15000
M204 S6000
G3 X107.369 Y106.226 I1.917 J-1.24 E.00069
; WIPE_START
G1 X107.451 Y106.362 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X107.466 Y105.088 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.0962902
G1 F15000
M204 S6000
G2 X107.313 Y105.339 I3.193 J2.117 E.00128
; WIPE_START
G1 X107.466 Y105.088 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X108.2 Y104.08 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.228632
G1 F15000
M204 S6000
G1 X108.058 Y104.074 E.00215
G2 X107.739 Y104.402 I2.131 J2.388 E.00693
; WIPE_START
G1 X108.058 Y104.074 E-.57962
G1 X108.2 Y104.08 E-.18038
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X109.606 Y103.571 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.11782
G1 F15000
M204 S6000
G1 X109.413 Y103.649 E.00127
; WIPE_START
G1 X109.606 Y103.571 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.272 Y106.837 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.20223
G1 F15000
M204 S6000
G1 X111.286 Y106.98 E.00186
G3 X110.625 Y107.627 I-3.738 J-3.154 E.01203
; WIPE_START
G1 X110.882 Y107.407 E-.24044
G1 X111.286 Y106.98 E-.41795
G1 X111.272 Y106.837 E-.10161
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X108.952 Y107.842 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.0931843
G1 F15000
M204 S6000
G3 X108.821 Y107.762 I1.053 J-1.868 E.00063
; WIPE_START
G1 X108.952 Y107.842 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X111.651 Y110.086 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.192495
G1 F15000
M204 S6000
G1 X111.528 Y110.171 E.00183
; LINE_WIDTH: 0.150762
G1 X111.404 Y110.255 E.00132
; LINE_WIDTH: 0.109028
G1 X111.28 Y110.34 E.00081
M204 S10000
G1 X109.411 Y112.487 F42000
; LINE_WIDTH: 0.118629
G1 F15000
M204 S6000
G1 X109.411 Y112.841 E.00218
M204 S10000
G1 X109.494 Y110.437 F42000
; LINE_WIDTH: 0.101457
G1 F15000
M204 S6000
G1 X109.402 Y110.551 E.0007
G1 X109.374 Y110.527 E.00018
; WIPE_START
G1 X109.402 Y110.551 E-.15422
G1 X109.494 Y110.437 E-.60578
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.952 Y104.242 Z3.6 F42000
G1 X116.259 Y101.036 Z3.6
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.0890835
G1 F15000
M204 S6000
G1 X116.011 Y101.284 E.00132
; WIPE_START
G1 X116.259 Y101.036 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X114.067 Y107.554 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; LINE_WIDTH: 0.108951
G1 F15000
M204 S6000
G1 X113.982 Y107.678 E.00081
; LINE_WIDTH: 0.15051
G1 X113.896 Y107.801 E.00132
; LINE_WIDTH: 0.19207
G1 X113.811 Y107.925 E.00183
M204 S10000
G1 X113.323 Y108.834 F42000
; LINE_WIDTH: 0.101834
G1 F15000
M204 S6000
G3 X112.559 Y109.599 I-9.759 J-8.975 E.00519
; WIPE_START
G1 X112.949 Y109.23 E-.37715
G1 X113.323 Y108.834 E-.38285
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.515 Y106.907 Z3.6 F42000
G1 Z3.2
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G2 X116.528 Y106.83 I-.36 J-.101 E.0026
G1 X116.705 Y106.83 E.00588
G3 X116.733 Y108.201 I-4.763 J.782 E.04563
G1 X116.291 Y107.835 E.01902
G3 X115.541 Y109.498 I-7.049 J-2.181 E.06066
G3 X116.731 Y110.361 I-4.199 J7.041 E.04882
G1 X116.733 Y112.394 E.06745
G1 X116.206 Y111.958 E.02267
G2 X114.634 Y111.633 I-1.008 J.912 E.05697
G3 X113.586 Y112.457 I-7.947 J-9.036 E.04424
G1 X113.044 Y112.534 E.01814
G1 X113.044 Y114.632 E.06962
G1 X113.586 Y114.49 E.01857
G1 X114.11 Y114.054 E.0226
G3 X115.682 Y113.73 I1.008 J.912 E.05697
G2 X116.731 Y114.554 I7.947 J-9.036 E.04424
G1 X116.733 Y116.587 E.06745
G1 X116.206 Y116.151 E.02267
G2 X114.634 Y115.827 I-1.008 J.912 E.05698
G3 X113.586 Y116.65 I-7.95 J-9.04 E.04424
G3 X112.279 Y116.372 I-.408 J-1.292 E.04635
G1 X112.279 Y118.555 E.07243
G2 X113.586 Y118.683 I.757 J-.997 E.04585
G1 X114.11 Y118.248 E.0226
G3 X115.682 Y117.923 I1.008 J.912 E.05697
G2 X116.731 Y118.747 I7.95 J-9.04 E.04424
G1 X116.733 Y119.16 E.0137
G1 X116.63 Y119.232 E.00417
G1 X115.552 Y119.232 E.03575
M204 S10000
G1 X112.168 Y119.626 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.42396
G1 F9447.828
M204 S6000
G1 X116.627 Y119.626 E.13845
M204 S10000
G1 X112.168 Y119.626 F42000
; LINE_WIDTH: 0.378932
G1 F10713.918
M204 S6000
G1 X112.038 Y119.565 E.00392
G1 X111.91 Y119.372 E.00635
G1 X111.909 Y115.043 E.11851
G1 X111.576 Y115.043 E.00913
G1 X111.582 Y119.643 E.12595
G1 X112.108 Y119.627 E.01442
; CHANGE_LAYER
; Z_HEIGHT: 3.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F10713.918
G1 X111.582 Y119.643 E-.20014
G1 X111.58 Y118.17 E-.55986
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 17/79
; update layer progress
M73 L17
M991 S0 P16 ;notify layer change
M106 S201.45
; OBJECT_ID: 105
M204 S10000
G17
G3 Z3.6 I1.128 J.456 P1  F42000
G1 X116.822 Y105.192 Z3.6
G1 Z3.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.119 Y107.262 E.06937
G1 X117.119 Y119.998 E.4225
G1 X111.243 Y119.998 E.19491
G1 X111.243 Y110.776 E.30592
G1 X111.369 Y110.736 E.00437
G2 X114.754 Y105.029 I-1.914 J-4.993 E.23744
G1 X116.799 Y105.029 E.06782
G1 X116.814 Y105.132 E.00346
M204 S10000
G1 X117.16 Y104.678 F42000
G1 F8843.478
M204 S6000
G1 X117.526 Y107.233 E.08561
G1 X117.526 Y120.066 E.42571
G1 X117.414 Y120.406 E.01186
G1 X110.836 Y120.406 E.21819
G1 X110.836 Y110.479 E.32927
G2 X114.264 Y104.622 I-1.367 J-4.731 E.24835
G1 X117.148 Y104.622 E.09567
M204 S10000
G1 X117.141 Y104.215 F42000
G1 F8843.478
M204 S6000
G1 X117.504 Y104.215 E.01205
G1 X117.933 Y107.204 E.10015
G1 X117.933 Y120.131 E.42884
G1 X117.708 Y120.813 E.0238
G1 X110.429 Y120.813 E.24146
G1 X110.429 Y110.16 E.35336
G2 X113.72 Y104.215 I-.956 J-4.412 E.25516
G1 X117.081 Y104.215 E.1115
M204 S10000
G1 X116.734 Y103.808 F42000
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.42801
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y103.808 E1.42801
G1 X117.857 Y103.808 E.00469
G1 X118.34 Y107.174 E.11282
G1 X118.34 Y120.197 E.43198
G1 X118.002 Y121.22 E.03573
G1 X110.022 Y121.22 E.26472
G1 X110.022 Y109.829 E.37784
G2 X113.103 Y103.808 I-.567 J-4.088 E.26294
G1 X116.674 Y103.808 E.11847
M204 S10000
G1 X116.327 Y103.401 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.42801
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y103.401 E1.42801
G1 X118.21 Y103.401 E.00289
G1 X118.747 Y107.145 E.12548
G1 X118.747 Y120.262 E.43511
G1 X118.297 Y121.627 E.04766
G1 X109.615 Y121.627 E.28799
G1 X109.615 Y109.453 E.40383
G2 X112.338 Y103.401 I-.151 J-3.707 E.2725
G1 X116.267 Y103.401 E.13034
M204 S250
G1 X115.935 Y103.009 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.32277
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y103.009 E1.32277
G1 X118.55 Y103.009 E.00107
G1 X119.139 Y107.117 E.12754
G1 X119.139 Y120.325 E.40584
G1 X118.58 Y122.019 E.0548
G1 X109.223 Y122.019 E.28752
G1 X109.223 Y109.048 E.39855
G2 X111.325 Y103.009 I.255 J-3.297 E.26683
G1 X115.875 Y103.009 E.13979
; WIPE_START
M204 S6000
G1 X115.878 Y101.009 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z3.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z3.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z3.8 F4000
            G39.3 S1
            G0 Z3.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.225 Y104.011 F42000
G1 Z3.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E2.01586
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.151 Y70.595 Z3.8 F42000
G1 X116.771 Y109.751 Z3.8
G1 Z3.4
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.771 Y108.123 E.05401
G3 X116.401 Y107.752 I.329 J-.697 E.01772
G3 X115.583 Y109.584 I-7.356 J-2.189 E.06675
G1 X115.682 Y109.635 E.00371
G2 X116.731 Y110.504 I2.023 J-1.373 E.04578
G1 X116.771 Y110.501 E.00134
G1 X116.771 Y112.316 E.06022
G1 X116.206 Y111.737 E.02682
G2 X114.634 Y111.731 I-.79 J.883 E.05703
G3 X113.586 Y112.6 I-2.023 J-1.373 E.04578
G1 X113.124 Y112.567 E.01537
G1 X113.124 Y114.627 E.06835
G2 X114.11 Y113.834 I-.607 J-1.763 E.04285
G3 X115.682 Y113.828 I.79 J.883 E.05703
G2 X116.731 Y114.697 I2.023 J-1.373 E.04578
G1 X116.771 Y114.694 E.00134
G1 X116.771 Y116.509 E.06022
G2 X115.682 Y115.62 I-2.195 J1.574 E.04718
G2 X114.11 Y116.483 I-.01 J1.846 E.06213
G3 X112.537 Y116.489 I-.79 J-.883 E.05703
G1 X112.431 Y116.375 E.00517
G1 X112.431 Y118.827 E.08132
G1 X112.537 Y118.89 E.00411
G2 X114.11 Y118.027 I.01 J-1.846 E.06213
G3 X115.682 Y118.021 I.79 J.883 E.05703
G2 X116.731 Y118.89 I2.023 J-1.373 E.04578
G1 X116.771 Y119.075 E.00628
G1 X116.668 Y119.147 E.00417
G1 X115.366 Y119.147 E.0432
M204 S10000
G1 X112.32 Y119.573 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X116.633 Y119.573 E.15622
M204 S10000
G1 X112.285 Y114.712 F42000
; LINE_WIDTH: 0.42232
M73 P62 R9
G1 F9488.68
M204 S6000
G1 X112.731 Y114.689 E.01382
G1 X112.731 Y111.896 E.08635
G1 X112.842 Y111.678 E.00756
G1 X113.705 Y111.101 E.03209
G2 X116.199 Y106.875 I-4.336 J-5.409 E.15506
G1 X116.289 Y106.638 E.00782
G1 X116.5 Y106.517 E.00753
G1 X116.616 Y106.517 E.00359
G1 X116.459 Y105.421 E.03423
G1 X115.215 Y105.421 E.03847
G3 X114.281 Y108.862 I-6.184 J.169 E.11179
G3 X111.635 Y111.037 I-4.732 J-3.058 E.10761
G2 X111.642 Y114.99 I136.252 J1.75 E.12221
G1 X111.648 Y119.594 E.14234
; LINE_WIDTH: 0.468371
G1 F8461.615
G1 X112.32 Y119.573 E.02332
G1 X112.17 Y119.501 E.00577
; LINE_WIDTH: 0.433514
G1 F9216.735
G1 X112.034 Y119.292 E.00794
G1 X112.032 Y119.258 E.00108
G1 X112.032 Y114.99 E.13584
G1 X112.093 Y114.856 E.00469
G1 X112.237 Y114.748 E.00572
M204 S10000
G1 X112.004 Y114.463 F42000
; LINE_WIDTH: 0.40242
G1 F10013.908
M204 S6000
G1 X112.217 Y114.35 E.00706
G1 X112.363 Y114.34 E.0043
G1 X112.363 Y111.896 E.0716
; LINE_WIDTH: 0.41665
G1 F9632.622
G1 X112.41 Y111.713 E.00576
; LINE_WIDTH: 0.436412
G1 F9148.857
G1 X112.456 Y111.529 E.00607
G1 X112.685 Y111.34 E.00954
; LINE_WIDTH: 0.402306
G1 F10017.088
G1 X113.489 Y110.802 E.02832
G2 X115.839 Y106.8 I-4.118 J-5.11 E.13892
; LINE_WIDTH: 0.421049
G1 F9520.577
G1 X115.896 Y106.638 E.0053
; LINE_WIDTH: 0.461245
G1 F8605.749
G1 X115.953 Y106.476 E.00587
; LINE_WIDTH: 0.501442
G1 F7851.319
G1 X116.011 Y106.313 E.00643
; LINE_WIDTH: 0.531776
G1 F7364.143
G1 X116.135 Y106.218 E.00623
G1 X116.083 Y105.855 E.0146
G1 X115.627 Y105.855 E.01815
G1 X115.617 Y106.107 E.01002
; LINE_WIDTH: 0.502244
G1 F7837.616
G1 X115.58 Y106.275 E.00646
; LINE_WIDTH: 0.46365
G1 F8556.556
G1 X115.543 Y106.444 E.00592
; LINE_WIDTH: 0.404561
G1 F9954.622
G2 X115.369 Y107.294 I24.274 J5.407 E.02557
G3 X112.261 Y111.185 I-6.041 J-1.638 E.15095
; LINE_WIDTH: 0.440467
G1 F9055.533
G1 X112.037 Y111.305 E.00821
G1 X112.004 Y111.896 E.01919
; LINE_WIDTH: 0.40242
G1 F10013.908
G1 X112.004 Y114.403 E.07343
; WIPE_START
G1 X112.004 Y112.403 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X106.773 Y106.845 Z3.8 F42000
G1 X61.516 Y58.759 Z3.8
G1 Z3.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X61.025 Y58.963 Z3.8 F42000
G1 Z3.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; CHANGE_LAYER
; Z_HEIGHT: 3.6
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F6264.574
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 18/79
; update layer progress
M73 L18
M991 S0 P17 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z3.8 I1.217 J.018 P1  F42000
G1 X61.516 Y58.759 Z3.8
G1 Z3.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z4 F4000
            G39.3 S1
            G0 Z4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z3.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z4 F42000
G1 X116.734 Y101.741 Z4
G1 Z3.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z4 F42000
G1 Z3.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.783 Y70.582 Z4 F42000
G1 X114.775 Y105.224 Z4
G1 Z3.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.827 Y105.224 E.06805
G1 X117.157 Y107.525 E.07711
G1 X117.157 Y119.914 E.41094
G1 X111.395 Y119.914 E.19112
G1 X111.395 Y110.723 E.30486
G2 X114.781 Y105.284 I-1.933 J-4.977 E.22793
M204 S10000
G1 X114.306 Y104.817 F42000
G1 F8843.478
M204 S6000
G1 X117.18 Y104.817 E.09532
G1 X117.564 Y107.496 E.08978
G1 X117.564 Y119.951 E.41315
G1 X117.442 Y120.321 E.0129
G1 X110.988 Y120.321 E.21408
G1 X110.988 Y110.431 E.32806
G2 X114.317 Y104.876 I-1.516 J-4.683 E.23444
M204 S10000
G1 X113.783 Y104.41 F42000
G1 F8843.478
M204 S6000
G1 X117.532 Y104.41 E.12437
G1 X117.971 Y107.467 E.10245
G1 X117.971 Y120.017 E.41629
G1 X117.736 Y120.728 E.02484
G1 X110.581 Y120.728 E.23734
G1 X110.581 Y110.134 E.35141
G2 X113.801 Y104.468 I-1.115 J-4.381 E.24144
M204 S10000
G1 X113.19 Y104.003 F42000
G1 F8843.478
M204 S6000
G1 X117.885 Y104.003 E.15576
G1 X118.378 Y107.438 E.11512
G1 X118.378 Y120.082 E.41943
G1 X118.03 Y121.135 E.03677
G1 X110.174 Y121.135 E.26061
G1 X110.174 Y109.798 E.37608
G2 X113.215 Y104.058 I-.691 J-4.042 E.24871
M204 S10000
G1 X112.497 Y103.596 F42000
G1 F8843.478
M204 S6000
G1 X118.238 Y103.596 E.19043
G1 X118.785 Y107.409 E.12778
G1 X118.785 Y120.148 E.42256
G1 X118.325 Y121.542 E.0487
G1 X109.767 Y121.542 E.28387
G1 X109.767 Y109.438 E.40152
G2 X112.531 Y103.645 I-.313 J-3.705 E.25688
M204 S250
G1 X111.815 Y103.411 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G2 X111.587 Y103.204 I-2.338 J2.34 E.00946
G1 X118.578 Y103.204 E.2148
G1 X118.59 Y103.288 E.00261
M73 P63 R9
G1 X119.177 Y107.381 E.12706
G1 X119.177 Y120.211 E.39422
G1 X118.608 Y121.934 E.05576
G1 X109.375 Y121.934 E.28371
G1 X109.375 Y109.057 E.39568
G2 X111.857 Y103.454 I.102 J-3.306 E.24081
; WIPE_START
M204 S6000
G1 X111.587 Y103.204 E-.13972
G1 X113.22 Y103.204 E-.62028
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.809 Y109.71 Z4 F42000
G1 Z3.6
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.809 Y108.081 E.05401
G3 X116.454 Y107.581 I.512 J-.739 E.02078
G3 X115.561 Y109.622 I-6.836 J-1.774 E.07422
G1 X115.682 Y109.716 E.00511
G1 X116.206 Y110.549 E.03265
G2 X116.809 Y110.676 I.406 J-.438 E.02144
G1 X116.809 Y112.274 E.05302
G1 X116.206 Y111.381 E.03575
G1 X115.944 Y111.215 E.01029
G2 X114.634 Y111.813 I.112 J1.98 E.04889
G1 X114.11 Y112.646 E.03265
G1 X113.848 Y112.812 E.01029
G3 X113.124 Y112.642 I-.066 J-1.35 E.025
G1 X113.124 Y114.67 E.06725
G1 X113.586 Y114.31 E.01942
G1 X114.11 Y113.477 E.03265
G1 X114.372 Y113.312 E.01029
G3 X115.682 Y113.909 I-.112 J1.98 E.04889
G1 X116.206 Y114.742 E.03265
G2 X116.809 Y114.869 I.406 J-.438 E.02144
G1 X116.809 Y116.467 E.05302
G1 X116.206 Y115.574 E.03575
G1 X115.944 Y115.408 E.01029
G2 X114.634 Y116.006 I.112 J1.98 E.04889
G1 X114.11 Y116.839 E.03265
G1 X113.848 Y117.005 E.01029
G3 X112.583 Y116.442 I.103 J-1.936 E.04696
G1 X112.583 Y119.062 E.08691
G2 X113.586 Y118.503 I-.449 J-1.985 E.03861
G1 X114.11 Y117.67 E.03265
G1 X114.372 Y117.505 E.01029
G3 X115.682 Y118.103 I-.112 J1.981 E.04889
G1 X116.206 Y118.936 E.03265
G1 X116.407 Y119.062 E.00785
G1 X114.778 Y119.062 E.05401
M204 S10000
G1 X112.472 Y119.488 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X116.671 Y119.488 E.15208
M204 S10000
G1 X112.472 Y119.488 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X112.322 Y119.416 E.0059
; LINE_WIDTH: 0.423992
G1 F9447.045
G1 X112.186 Y119.207 E.00774
G1 X112.184 Y119.173 E.00106
G1 X112.184 Y114.99 E.1299
G1 X112.245 Y114.856 E.00458
G1 X112.411 Y114.719 E.00669
G1 X112.731 Y114.689 E.00998
G1 X112.731 Y111.896 E.08673
G1 X112.842 Y111.678 E.00759
G1 X113.724 Y111.086 E.03298
G2 X116.2 Y106.872 I-4.367 J-5.4 E.15511
G1 X116.289 Y106.638 E.00775
G1 X116.5 Y106.517 E.00756
G1 X116.616 Y106.517 E.00361
G1 X116.487 Y105.616 E.02826
G1 X115.191 Y105.616 E.04023
G3 X111.787 Y110.979 I-5.677 J.158 E.20931
G2 X111.794 Y114.99 I138.285 J1.778 E.12455
G1 X111.8 Y119.509 E.14034
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X112.412 Y119.49 E.02112
M204 S10000
G1 X112.259 Y111.896 F42000
; LINE_WIDTH: 0.60992
G1 F6349.207
M204 S6000
G1 X112.259 Y114.212 E.10699
M204 S10000
G1 X112.259 Y111.896 F42000
; LINE_WIDTH: 0.587363
G1 F6612.269
M204 S6000
G1 X112.323 Y111.789 E.00553
; LINE_WIDTH: 0.542248
G1 F7209.697
G1 X112.387 Y111.682 E.00507
; LINE_WIDTH: 0.497133
G1 F7925.806
G1 X112.451 Y111.575 E.00461
; LINE_WIDTH: 0.452018
G1 F8799.858
G1 X112.515 Y111.469 E.00415
; LINE_WIDTH: 0.403614
G1 F9980.77
G2 X113.508 Y110.788 I-6.945 J-11.189 E.0354
G2 X115.84 Y106.797 I-4.146 J-5.099 E.13882
; LINE_WIDTH: 0.420755
G1 F9527.969
G1 X115.903 Y106.592 E.0066
; LINE_WIDTH: 0.476356
G1 F8305.726
G1 X115.965 Y106.387 E.00757
G1 X116.164 Y106.234 E.00886
G1 X116.134 Y106.023 E.00752
G1 X115.6 Y106.023 E.01886
; LINE_WIDTH: 0.461308
G1 F8604.463
G1 X115.553 Y106.318 E.01016
; LINE_WIDTH: 0.406882
G1 F9891.161
G3 X115.174 Y107.906 I-8.674 J-1.231 E.04848
G3 X112.169 Y111.228 I-5.82 J-2.244 E.1359
G1 X112.179 Y111.541 E.0093
; LINE_WIDTH: 0.468835
G1 F8452.391
G1 X112.196 Y111.615 E.00264
; LINE_WIDTH: 0.509145
G1 F7721.593
G1 X112.212 Y111.689 E.00289
; LINE_WIDTH: 0.549455
G1 F7107.11
G1 X112.229 Y111.764 E.00313
; LINE_WIDTH: 0.589765
G1 F6583.219
G1 X112.246 Y111.838 E.00338
; CHANGE_LAYER
; Z_HEIGHT: 3.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F6583.219
G1 X112.229 Y111.764 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 19/79
; update layer progress
M73 L19
M991 S0 P18 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z4 I.879 J-.841 P1  F42000
G1 X61.516 Y58.759 Z4
G1 Z3.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z4.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z4.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z4.2 F4000
            G39.3 S1
            G0 Z4.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z3.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z4.2 F42000
G1 X116.734 Y101.741 Z4.2
G1 Z3.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z4.2 F42000
G1 Z3.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.79 Y70.583 Z4.2 F42000
G1 X114.801 Y105.42 Z4.2
G1 Z3.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.855 Y105.42 E.06814
G1 X117.195 Y107.789 E.07941
G1 X117.195 Y119.829 E.39938
G1 X111.547 Y119.829 E.18733
G1 X111.547 Y110.656 E.3043
G2 X114.804 Y105.479 I-2.085 J-4.924 E.21595
M204 S10000
G1 X114.344 Y105.012 F42000
G1 F8843.478
M204 S6000
G1 X117.208 Y105.012 E.095
G1 X117.602 Y107.76 E.09208
G1 X117.602 Y119.837 E.4006
G1 X117.47 Y120.236 E.01394
G1 X111.14 Y120.236 E.20997
G1 X111.14 Y110.39 E.32662
G2 X114.352 Y105.072 I-1.684 J-4.646 E.22285
M204 S10000
G1 X113.843 Y104.605 F42000
G1 F8843.478
M204 S6000
G1 X117.56 Y104.605 E.12331
G1 X118.009 Y107.731 E.10475
G1 X118.009 Y119.902 E.40374
G1 X117.764 Y120.643 E.02588
G1 X110.733 Y120.643 E.23323
G1 X110.733 Y110.085 E.35024
G2 X113.858 Y104.664 I-1.265 J-4.34 E.22923
M204 S10000
G1 X113.287 Y104.198 F42000
G1 F8843.478
M204 S6000
G1 X117.913 Y104.198 E.15346
G1 X118.416 Y107.702 E.11741
G1 X118.416 Y119.968 E.40687
G1 X118.058 Y121.05 E.03781
G1 X110.326 Y121.05 E.2565
G1 X110.326 Y109.766 E.37431
G2 X113.309 Y104.254 I-.861 J-4.029 E.23623
M204 S10000
G1 X112.614 Y103.791 F42000
G1 F8843.478
M204 S6000
G1 X118.266 Y103.791 E.18748
G1 X118.823 Y107.673 E.13008
G1 X118.823 Y120.033 E.41001
G1 X118.353 Y121.457 E.04974
M73 P63 R8
G1 X109.919 Y121.457 E.27976
G1 X109.919 Y109.422 E.39923
G2 X112.646 Y103.842 I-.441 J-3.671 E.24452
M204 S250
G1 X112.057 Y103.68 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G2 X111.804 Y103.399 I-2.584 J2.069 E.01161
G1 X118.606 Y103.399 E.20899
G1 X119.215 Y107.645 E.1318
G1 X119.215 Y120.096 E.38259
G1 X118.636 Y121.849 E.05673
G1 X109.527 Y121.849 E.2799
G1 X109.529 Y109.059 E.39301
G2 X112.094 Y103.727 I-.055 J-3.31 E.22491
; WIPE_START
M204 S6000
G1 X111.804 Y103.399 E-.16623
G1 X113.367 Y103.399 E-.59377
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.799 Y111.019 Z4.2 F42000
G1 X113.826 Y111.497 Z4.2
G1 Z3.8
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
M73 P64 R8
G1 F8843.478
M204 S6000
G3 X113.124 Y111.965 I-2.638 J-3.198 E.02804
G1 X113.124 Y112.748 E.02599
G3 X113.778 Y113.586 I-.356 J.952 E.03709
G3 X113.124 Y114.754 I-1.9 J-.297 E.04535
G1 X113.124 Y114.86 E.00352
G1 X112.883 Y115.101 E.01131
G1 X112.735 Y115.101 E.0049
G1 X112.735 Y116.582 E.04915
G1 X112.837 Y116.731 E.00597
G1 X113.55 Y117.255 E.02935
G3 X113.778 Y117.779 I-.337 J.458 E.01986
G3 X113.082 Y118.977 I-1.874 J-.287 E.04706
G1 X115.856 Y118.977 E.09203
G2 X115.383 Y117.779 I-1.73 J-.009 E.0438
G1 X114.67 Y117.255 E.02935
G3 X114.442 Y116.731 I.337 J-.458 E.01986
G3 X115.646 Y115.158 I2.141 J.392 E.06821
G2 X115.874 Y114.634 I-.337 J-.458 E.01986
G2 X114.67 Y113.062 I-2.141 J.392 E.06821
G3 X114.442 Y112.538 I.337 J-.458 E.01986
G3 X115.646 Y110.965 I2.141 J.392 E.06821
G2 X115.874 Y110.441 I-.337 J-.458 E.01986
G2 X115.551 Y109.638 I-1.233 J.029 E.02934
G2 X116.596 Y106.909 I-6.001 J-3.86 E.0976
G1 X116.663 Y106.909 E.00225
G2 X116.539 Y107.296 I.27 J.301 E.01413
G2 X116.846 Y108.128 I1.609 J-.123 E.0298
G1 X116.846 Y110.76 E.08733
G3 X116.57 Y111.227 I-.976 J-.263 E.01822
G2 X116.846 Y112.321 I1.7 J.152 E.03814
G1 X116.846 Y114.953 E.08733
G3 X116.57 Y115.42 I-.976 J-.263 E.01822
G2 X116.846 Y116.514 I1.7 J.152 E.03814
G1 X116.846 Y118.142 E.05401
M204 S10000
G1 X112.624 Y119.403 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X116.709 Y119.403 E.14795
M204 S10000
G1 X112.624 Y119.403 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X112.474 Y119.331 E.0059
; LINE_WIDTH: 0.424018
G1 F9446.392
G1 X112.338 Y119.122 E.00774
G1 X112.336 Y119.088 E.00106
G1 X112.336 Y114.99 E.12727
G3 X112.731 Y114.689 I.41 J.129 E.01644
G1 X112.731 Y111.896 E.08674
G1 X112.799 Y111.728 E.00563
G1 X113.729 Y111.083 E.03515
G2 X116.2 Y106.872 I-4.376 J-5.398 E.15492
G1 X116.248 Y106.687 E.00592
G1 X116.393 Y106.55 E.00619
G1 X116.616 Y106.517 E.007
G1 X116.515 Y105.812 E.02214
G1 X115.192 Y105.812 E.04108
G1 X115.164 Y106.334 E.01624
G1 X115.01 Y107.217 E.02783
G3 X111.939 Y110.902 I-5.489 J-1.451 E.1538
G2 X111.946 Y114.99 I140.895 J1.817 E.12694
G1 X111.952 Y119.424 E.13771
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X112.564 Y119.405 E.02112
M204 S10000
G1 X112.335 Y111.896 F42000
; LINE_WIDTH: 0.45792
G1 F8674.698
M204 S6000
G1 X112.335 Y114.329 E.08227
M204 S10000
G1 X112.335 Y111.896 F42000
; LINE_WIDTH: 0.434925
G1 F9183.556
M204 S6000
G1 X112.477 Y111.541 E.0122
; LINE_WIDTH: 0.406625
G1 F9898.134
G1 X112.684 Y111.338 E.00861
G1 X113.513 Y110.783 E.02956
G2 X115.84 Y106.797 I-4.152 J-5.095 E.13978
G1 X115.914 Y106.494 E.00925
G1 X116.164 Y106.197 E.01148
G1 X115.566 Y106.197 E.01772
G3 X113.355 Y110.447 I-6.259 J-.557 E.14565
G3 X112.312 Y111.128 I-3.594 J-4.364 E.03699
; LINE_WIDTH: 0.434925
G1 F9183.556
G1 X112.334 Y111.836 E.02263
; CHANGE_LAYER
; Z_HEIGHT: 4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9183.556
G1 X112.312 Y111.128 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 20/79
; update layer progress
M73 L20
M991 S0 P19 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z4.2 I.874 J-.847 P1  F42000
G1 X61.516 Y58.759 Z4.2
G1 Z4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z4.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z4.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z4.4 F4000
            G39.3 S1
            G0 Z4.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z4.4 F42000
G1 X116.734 Y101.741 Z4.4
G1 Z4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z4.4 F42000
G1 Z4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.792 Y70.583 Z4.4 F42000
G1 X114.802 Y105.615 Z4.4
G1 Z4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.883 Y105.615 E.06903
G1 X117.233 Y108.053 E.08171
G1 X117.233 Y119.744 E.38781
G1 X111.699 Y119.744 E.18354
G1 X111.699 Y110.59 E.30367
G2 X114.803 Y105.675 I-2.204 J-4.829 E.20405
M204 S10000
G1 X114.364 Y105.208 F42000
G1 F8843.478
M204 S6000
G1 X117.236 Y105.208 E.09525
G1 X117.64 Y108.024 E.09438
G1 X117.64 Y119.722 E.38805
G1 X117.498 Y120.151 E.01499
G1 X111.292 Y120.151 E.20585
G1 X111.292 Y110.327 E.32589
G2 X114.371 Y105.267 I-1.815 J-4.571 E.21082
M204 S10000
G1 X113.887 Y104.801 F42000
G1 F8843.478
M204 S6000
G1 X117.588 Y104.801 E.12279
G1 X118.047 Y107.995 E.10704
G1 X118.047 Y119.788 E.39119
G1 X117.792 Y120.558 E.02692
G1 X110.885 Y120.558 E.22912
G1 X110.885 Y110.037 E.34902
G2 X113.899 Y104.859 I-1.412 J-4.288 E.21728
M204 S10000
G1 X113.35 Y104.394 F42000
G1 F8843.478
M204 S6000
G1 X117.941 Y104.394 E.15231
G1 X118.454 Y107.966 E.11971
G1 X118.454 Y119.853 E.39432
G1 X118.086 Y120.965 E.03885
G1 X110.478 Y120.965 E.25238
G1 X110.478 Y109.738 E.37243
G2 X113.369 Y104.45 I-1.016 J-3.99 E.22426
M204 S10000
G1 X112.738 Y103.986 F42000
G1 F8843.478
M204 S6000
G1 X118.294 Y103.986 E.1843
G1 X118.319 Y104.157 E.00572
G1 X118.861 Y107.937 E.12666
G1 X118.861 Y119.919 E.39746
G1 X118.381 Y121.372 E.05079
G1 X110.071 Y121.372 E.27565
G1 X110.071 Y109.404 E.39701
G2 X112.766 Y104.04 I-.613 J-3.667 E.23178
M204 S250
G1 X111.986 Y103.594 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.634 Y103.594 E.20427
G1 X118.707 Y104.102 E.01574
G1 X119.253 Y107.909 E.11819
G1 X119.253 Y119.982 E.37096
G1 X118.664 Y121.764 E.05769
G1 X109.679 Y121.764 E.27609
G1 X109.679 Y109.052 E.3906
G2 X112.025 Y103.64 I-.209 J-3.305 E.22359
; WIPE_START
M204 S6000
G1 X114.025 Y103.626 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.702 Y111.252 Z4.4 F42000
G1 X113.688 Y111.597 Z4.4
G1 Z4
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G3 X113.124 Y111.965 I-2.091 J-2.588 E.02238
G1 X113.124 Y112.919 E.03164
G3 X113.599 Y113.586 I-1.376 J1.485 E.02737
G3 X112.887 Y115.131 I-1.689 J.158 E.05911
G1 X112.887 Y116.87 E.05769
G3 X113.599 Y117.779 I-1.843 J2.178 E.03858
G3 X113.308 Y118.893 I-1.651 J.163 E.039
G1 X115.654 Y118.893 E.07781
G1 X115.696 Y118.827 E.00258
G2 X114.956 Y117.255 I-1.713 J-.154 E.06042
G1 X114.62 Y116.731 E.02065
G3 X115.36 Y115.158 I1.713 J-.154 E.06042
G1 X115.696 Y114.634 E.02065
G2 X114.956 Y113.062 I-1.713 J-.154 E.06042
G1 X114.62 Y112.538 E.02065
G3 X115.36 Y110.965 I1.713 J-.154 E.06042
G1 X115.696 Y110.441 E.02065
G2 X115.565 Y109.614 I-1.014 J-.263 E.02856
G2 X116.572 Y107.018 I-5.876 J-3.774 E.093
G1 X116.732 Y107.018 E.0053
G3 X116.716 Y107.82 I-6.267 J.277 E.02663
G1 X116.884 Y108.207 E.01398
G1 X116.884 Y111.144 E.09745
G2 X116.884 Y112.4 I1.091 J.628 E.0436
G1 X116.884 Y115.337 E.09745
G2 X116.884 Y116.593 I1.091 J.628 E.0436
G1 X116.884 Y118.221 E.05401
M204 S10000
G1 X112.776 Y119.318 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X116.747 Y119.318 E.14382
M204 S10000
G1 X112.776 Y119.318 F42000
; LINE_WIDTH: 0.4774
M73 P65 R8
G1 F8285.767
M204 S6000
G1 X112.626 Y119.246 E.0059
; LINE_WIDTH: 0.434251
G1 F9199.371
G1 X112.49 Y119.037 E.00795
G1 X112.488 Y119.003 E.00108
G1 X112.488 Y114.99 E.12798
; LINE_WIDTH: 0.452882
G1 F8781.309
G1 X112.52 Y114.906 E.00299
; LINE_WIDTH: 0.492325
G1 F8010.592
G1 X112.551 Y114.822 E.00328
; LINE_WIDTH: 0.550896
G1 F7086.957
G3 X112.666 Y114.663 I.212 J.031 E.00845
G1 X112.666 Y111.896 E.11452
; LINE_WIDTH: 0.529574
G1 F7397.463
G1 X112.749 Y111.808 E.0048
; LINE_WIDTH: 0.48574
G1 F8129.714
G1 X112.832 Y111.72 E.00437
; LINE_WIDTH: 0.420163
G1 F9542.922
G1 X112.915 Y111.632 E.00372
G1 X113.687 Y111.113 E.02859
G2 X116.208 Y106.846 I-4.338 J-5.442 E.15577
G3 X116.398 Y106.645 I.352 J.142 E.0087
G1 X116.632 Y106.626 E.00721
G1 X116.543 Y106.007 E.01924
G1 X115.181 Y106.007 E.04187
G1 X115.145 Y106.521 E.01584
G3 X112.091 Y110.832 I-5.673 J-.781 E.16879
G1 X112.091 Y111.538 E.0217
; LINE_WIDTH: 0.441907
G1 F9022.858
G1 X112.113 Y111.657 E.00395
; LINE_WIDTH: 0.48574
G1 F8129.714
G1 X112.135 Y111.777 E.00438
; LINE_WIDTH: 0.550532
G1 F7092.038
G1 X112.157 Y111.896 E.00502
G1 X112.157 Y114.55 E.10977
; LINE_WIDTH: 0.531769
G1 F7364.248
G1 X112.137 Y114.697 E.00589
; LINE_WIDTH: 0.492325
G1 F8010.592
G1 X112.118 Y114.843 E.00542
; LINE_WIDTH: 0.434247
G1 F9199.477
G1 X112.098 Y114.99 E.00472
G1 X112.104 Y119.34 E.1387
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X112.716 Y119.32 E.02112
M204 S10000
G1 X112.461 Y111.576 F42000
; LINE_WIDTH: 0.40469
G1 F9951.082
M204 S6000
G1 X112.731 Y111.312 E.01115
G1 X113.471 Y110.815 E.02629
G2 X115.846 Y106.769 I-4.103 J-5.128 E.14141
G1 X115.879 Y106.65 E.00364
G1 X116.114 Y106.384 E.01048
G1 X115.532 Y106.384 E.01715
G1 X115.371 Y107.286 E.02703
G3 X112.461 Y111.049 I-5.846 J-1.514 E.14414
G1 X112.461 Y111.516 E.01377
; CHANGE_LAYER
; Z_HEIGHT: 4.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9951.082
G1 X112.461 Y111.049 E-.17754
G1 X112.808 Y110.851 E-.15206
G1 X113.311 Y110.484 E-.23675
G1 X113.686 Y110.138 E-.19365
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 21/79
; update layer progress
M73 L21
M991 S0 P20 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z4.4 I.854 J-.867 P1  F42000
G1 X61.516 Y58.759 Z4.4
G1 Z4.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z4.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z4.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z4.6 F4000
            G39.3 S1
            G0 Z4.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z4.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z4.6 F42000
G1 X116.734 Y101.741 Z4.6
G1 Z4.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z4.6 F42000
G1 Z4.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.795 Y70.583 Z4.6 F42000
G1 X114.806 Y105.81 Z4.6
G1 Z4.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.911 Y105.81 E.06981
G1 X117.27 Y108.317 E.08401
G1 X117.27 Y119.542 E.37236
G1 X117.232 Y119.659 E.00409
G1 X111.851 Y119.659 E.17847
G1 X111.851 Y110.521 E.30315
G2 X114.805 Y105.87 I-2.399 J-4.787 E.19196
M204 S10000
G1 X114.392 Y105.403 F42000
G1 F8843.478
M204 S6000
G1 X117.264 Y105.403 E.09527
G1 X117.677 Y108.288 E.09668
G1 X117.677 Y119.608 E.3755
G1 X117.526 Y120.066 E.01603
G1 X111.444 Y120.066 E.20174
G1 X111.444 Y110.258 E.32534
G2 X114.395 Y105.463 I-1.98 J-4.524 E.19876
M204 S10000
G1 X113.934 Y104.996 F42000
G1 F8843.478
M204 S6000
G1 X117.616 Y104.996 E.12217
G1 X118.084 Y108.259 E.10934
G1 X118.084 Y119.673 E.37863
G1 X117.82 Y120.473 E.02796
G1 X111.037 Y120.473 E.225
G1 X111.037 Y109.987 E.34786
G2 X113.943 Y105.055 I-1.578 J-4.252 E.20549
M204 S10000
G1 X113.421 Y104.589 F42000
G1 F8843.478
M204 S6000
G1 X117.969 Y104.589 E.15087
G1 X118.492 Y108.23 E.12201
G1 X118.492 Y119.738 E.38177
G1 X118.114 Y120.88 E.03989
G1 X110.63 Y120.88 E.24827
G1 X110.63 Y109.69 E.37121
G2 X113.438 Y104.646 I-1.166 J-3.952 E.21214
M204 S10000
G1 X112.826 Y104.182 F42000
G1 F8843.478
M204 S6000
G1 X118.322 Y104.182 E.18232
G1 X118.377 Y104.564 E.01281
G1 X118.899 Y108.201 E.12187
G1 X118.899 Y119.804 E.38491
G1 X118.409 Y121.288 E.05183
G1 X110.223 Y121.288 E.27153
G1 X110.223 Y109.372 E.39525
G2 X112.851 Y104.236 I-.753 J-3.626 E.2194
M204 S250
G1 X112.139 Y103.79 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.662 Y103.79 E.20042
G1 X118.765 Y104.508 E.02231
G1 X119.291 Y108.173 E.11375
G1 X119.291 Y119.867 E.35934
G1 X118.692 Y121.68 E.05865
G1 X109.831 Y121.68 E.27228
G1 X109.831 Y109.038 E.38844
G2 X112.174 Y103.838 I-.363 J-3.292 E.21115
; WIPE_START
M204 S6000
G1 X114.174 Y103.823 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X113.527 Y111.428 Z4.6 F42000
G1 X113.501 Y111.732 Z4.6
G1 Z4.2
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G3 X113.124 Y111.965 I-1.367 J-1.792 E.01474
G1 X113.124 Y113.149 E.03928
G3 X113.476 Y114.634 I-.938 J1.007 E.05367
G3 X113.039 Y115.196 I-40.638 J-31.199 E.02362
G1 X113.039 Y117.234 E.06763
G2 X113.468 Y117.779 I38.746 J-30.124 E.023
G3 X113.48 Y118.808 I-1.127 J.528 E.03519
G1 X115.569 Y118.808 E.06929
G2 X115.165 Y117.255 I-1.318 J-.486 E.05666
G1 X114.751 Y116.731 E.02215
G3 X115.151 Y115.158 I1.322 J-.501 E.05732
G1 X115.565 Y114.634 E.02215
G2 X115.165 Y113.062 I-1.322 J-.501 E.05732
G1 X114.751 Y112.538 E.02215
G3 X115.151 Y110.965 I1.322 J-.501 E.05732
G1 X115.565 Y110.441 E.02215
G2 X115.605 Y109.546 I-.966 J-.492 E.03065
G2 X116.531 Y107.214 I-5.686 J-3.609 E.08373
G1 X116.76 Y107.214 E.0076
G3 X116.731 Y107.82 I-.814 J.264 E.0206
G2 X116.922 Y108.673 I10.817 J-1.984 E.02898
G1 X116.922 Y111.174 E.08298
G2 X116.731 Y112.013 I39.428 J9.439 E.02856
G2 X116.922 Y112.866 I10.817 J-1.984 E.02898
G1 X116.922 Y115.367 E.08298
G2 X116.731 Y116.206 I39.428 J9.439 E.02856
G3 X116.922 Y118.687 I-7.41 J1.82 E.0829
M204 S10000
G1 X112.928 Y119.234 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X116.785 Y119.234 E.13968
M204 S10000
G1 X112.928 Y119.234 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X112.778 Y119.161 E.0059
; LINE_WIDTH: 0.450501
G1 F8832.608
G1 X112.642 Y118.953 E.00828
G1 X112.64 Y118.919 E.00113
G1 X112.64 Y114.894 E.13366
G1 X112.704 Y114.637 E.0088
G1 X112.704 Y111.896 E.09103
G1 X112.795 Y111.725 E.00642
; LINE_WIDTH: 0.420177
G1 F9542.569
G2 X114.292 Y110.583 I-4.742 J-7.765 E.058
G2 X116.18 Y107.001 I-4.803 J-4.821 E.12638
G1 X116.385 Y106.829 E.00822
G1 X116.66 Y106.821 E.00846
G1 X116.571 Y106.202 E.01924
G1 X115.168 Y106.202 E.04314
G3 X113.496 Y109.816 I-5.659 J-.424 E.12506
G3 X112.243 Y110.75 I-3.952 J-3.992 E.0482
G1 X112.243 Y111.297 E.01682
; LINE_WIDTH: 0.433865
G1 F9208.456
G1 X112.257 Y111.597 E.00955
; LINE_WIDTH: 0.450391
G1 F8834.982
G1 X112.271 Y111.896 E.00995
G1 X112.271 Y114.637 E.09101
G1 X112.25 Y114.894 E.00857
G1 X112.256 Y119.255 E.14479
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X112.868 Y119.235 E.02112
M204 S10000
G1 X112.612 Y111.413 F42000
; LINE_WIDTH: 0.404029
G1 F9969.287
M204 S6000
M73 P66 R8
G1 X113.465 Y110.819 E.03058
G2 X115.806 Y106.965 I-4.069 J-5.109 E.1355
G1 X115.843 Y106.84 E.00383
G1 X116.082 Y106.576 E.01047
G1 X115.512 Y106.576 E.01676
G3 X114.234 Y109.555 I-6.266 J-.924 E.09648
G3 X112.612 Y110.965 I-4.861 J-3.953 E.06355
G1 X112.612 Y111.353 E.01139
; CHANGE_LAYER
; Z_HEIGHT: 4.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9969.287
G1 X112.612 Y110.965 E-.14709
G1 X112.799 Y110.856 E-.08216
G1 X113.3 Y110.493 E-.23521
G1 X113.768 Y110.067 E-.24051
G1 X113.865 Y109.96 E-.05503
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 22/79
; update layer progress
M73 L22
M991 S0 P21 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z4.6 I.851 J-.87 P1  F42000
G1 X61.516 Y58.759 Z4.6
G1 Z4.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z4.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z4.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z4.8 F4000
            G39.3 S1
            G0 Z4.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z4.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z4.8 F42000
G1 X116.734 Y101.741 Z4.8
G1 Z4.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z4.8 F42000
G1 Z4.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.797 Y70.583 Z4.8 F42000
G1 X114.805 Y106.005 Z4.8
G1 Z4.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.939 Y106.005 E.07077
G1 X117.308 Y108.581 E.08631
G1 X117.308 Y119.428 E.35981
G1 X117.26 Y119.574 E.00513
G1 X112.003 Y119.574 E.17436
G1 X112.003 Y110.441 E.30296
G2 X114.802 Y106.065 I-2.563 J-4.722 E.17985
M204 S10000
G1 X114.393 Y105.598 F42000
G1 F8843.478
M204 S6000
G1 X117.292 Y105.598 E.09614
G1 X117.715 Y108.552 E.09897
G1 X117.715 Y119.493 E.36295
G1 X117.554 Y119.982 E.01707
G1 X111.596 Y119.982 E.19763
G1 X111.596 Y110.189 E.32483
G2 X114.395 Y105.658 I-2.108 J-4.432 E.18673
M204 S10000
G1 X113.952 Y105.191 F42000
G1 F8843.478
M204 S6000
G1 X117.644 Y105.191 E.12248
G1 X118.122 Y108.522 E.11164
G1 X118.122 Y119.558 E.36608
G1 X117.848 Y120.389 E.029
G1 X111.189 Y120.389 E.22089
G1 X111.189 Y109.928 E.347
G2 X113.959 Y105.251 I-1.723 J-4.18 E.19346
M204 S10000
G1 X113.468 Y104.784 F42000
G1 F8843.478
M204 S6000
G1 X117.997 Y104.784 E.15026
G1 X118.032 Y105.028 E.00819
G1 X118.529 Y108.493 E.11612
G1 X118.529 Y119.624 E.36922
G1 X118.142 Y120.796 E.04093
G1 X110.782 Y120.796 E.24416
G1 X110.782 Y109.649 E.36976
G2 X113.481 Y104.842 I-1.325 J-3.905 E.20027
M204 S10000
G1 X112.918 Y104.377 F42000
G1 F8843.478
M204 S6000
G1 X118.35 Y104.377 E.18019
G1 X118.435 Y104.971 E.01989
G1 X118.936 Y108.464 E.11708
G1 X118.936 Y119.689 E.37236
G1 X118.437 Y121.203 E.05287
G1 X110.375 Y121.203 E.26742
G1 X110.375 Y109.343 E.39341
G2 X112.94 Y104.433 I-.915 J-3.603 E.20734
M204 S250
G1 X112.275 Y103.985 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.69 Y103.985 E.19712
G1 X118.823 Y104.915 E.02887
G1 X119.329 Y108.436 E.10931
G1 X119.329 Y119.752 E.34771
G1 X118.72 Y121.595 E.05962
G1 X109.983 Y121.595 E.26847
G1 X109.983 Y109.02 E.38639
G2 X112.306 Y104.036 I-.514 J-3.273 E.19929
; WIPE_START
M204 S6000
G1 X114.306 Y104.02 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X114.484 Y108.426 Z4.8 F42000
G1 Z4.4
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G3 X113.517 Y109.728 I-5.012 J-2.711 E.05399
G3 X113.279 Y110.965 I-1.045 J.441 E.0443
G1 X113.191 Y111.054 E.00416
G1 X113.191 Y113.41 E.07816
G3 X113.191 Y115.247 I-.762 J.918 E.06953
G1 X113.191 Y117.603 E.07816
G3 X113.608 Y118.723 I-1.082 J1.041 E.04077
G1 X115.509 Y118.723 E.06306
G2 X115.376 Y117.255 I-.993 J-.65 E.05276
G3 X114.61 Y115.682 I.977 J-1.449 E.06077
G3 X115.462 Y114.634 I2.765 J1.378 E.04518
G2 X115.376 Y113.062 I-.936 J-.737 E.05707
G3 X114.61 Y111.489 I.977 J-1.449 E.06077
G3 X115.462 Y110.441 I2.765 J1.378 E.04518
G2 X115.376 Y108.869 I-.936 J-.737 E.05707
G1 X114.854 Y108.344 E.02453
G1 X114.691 Y107.984 E.01312
G2 X115.089 Y106.623 I-15.801 J-5.354 E.04704
G1 X115.357 Y106.353 E.01262
G1 X116.637 Y106.353 E.04245
G1 X116.815 Y107.596 E.04166
G2 X116.96 Y108.846 I1.143 J.501 E.04374
G3 X116.951 Y111.489 I-33.514 J1.203 E.0877
G2 X116.96 Y113.039 I1.108 J.768 E.05478
G3 X116.951 Y115.682 I-33.514 J1.203 E.0877
G2 X116.96 Y117.232 I1.108 J.768 E.05478
G1 X116.938 Y118.642 E.04676
G3 X116.785 Y118.723 I-.117 J-.036 E.00638
M204 S10000
G1 X113.08 Y119.149 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X116.822 Y119.149 E.13555
M204 S10000
G1 X113.08 Y119.149 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X112.93 Y119.077 E.0059
; LINE_WIDTH: 0.433537
G1 F9216.203
G1 X112.794 Y118.868 E.00794
G1 X112.792 Y118.834 E.00108
G1 X112.792 Y110.404 E.26831
G1 X112.402 Y110.663 E.01491
G1 X112.408 Y119.17 E.27078
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X113.02 Y119.151 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 4.6
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X112.408 Y119.17 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 23/79
; update layer progress
M73 L23
M991 S0 P22 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z4.8 I.931 J-.784 P1  F42000
G1 X61.516 Y58.759 Z4.8
G1 Z4.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z5 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z5
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z5 F4000
            G39.3 S1
            G0 Z5 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z4.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z5 F42000
G1 X116.734 Y101.741 Z5
G1 Z4.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z5 F42000
G1 Z4.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.795 Y70.583 Z5 F42000
G1 X114.783 Y106.2 Z5
G1 Z4.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.967 Y106.2 E.07244
G1 X117.346 Y108.844 E.0886
G1 X117.346 Y119.313 E.34726
M73 P67 R8
G1 X117.288 Y119.49 E.00617
G1 X112.155 Y119.49 E.17025
G1 X112.155 Y110.355 E.30303
G2 X114.778 Y106.26 I-2.682 J-4.605 E.16748
M204 S10000
G1 X114.395 Y105.793 F42000
G1 F8843.478
M204 S6000
G1 X117.32 Y105.793 E.09701
G1 X117.753 Y108.815 E.10127
G1 X117.753 Y119.378 E.3504
G1 X117.582 Y119.897 E.01811
G1 X111.748 Y119.897 E.19351
G1 X111.748 Y110.119 E.32436
G2 X114.394 Y105.853 I-2.288 J-4.373 E.17467
M204 S10000
G1 X113.98 Y105.386 F42000
G1 F8843.478
M204 S6000
G1 X117.672 Y105.386 E.12249
G1 X117.688 Y105.493 E.00357
G1 X118.16 Y108.786 E.11037
G1 X118.16 Y119.444 E.35353
G1 X117.876 Y120.304 E.03004
G1 X111.341 Y120.304 E.21678
G1 X111.341 Y109.859 E.34649
G2 X113.984 Y105.446 I-1.877 J-4.122 E.18144
M204 S10000
G1 X113.509 Y104.979 F42000
G1 F8843.478
M204 S6000
G1 X118.025 Y104.979 E.14981
G1 X118.091 Y105.435 E.01528
G1 X118.567 Y108.757 E.11133
G1 X118.567 Y119.509 E.35667
G1 X118.17 Y120.711 E.04197
G1 X110.934 Y120.711 E.24004
G1 X110.934 Y109.59 E.36891
G2 X113.52 Y105.038 I-1.475 J-3.848 E.18815
M204 S10000
G1 X112.982 Y104.572 F42000
G1 F8843.478
M204 S6000
G1 X118.378 Y104.572 E.17899
G1 X118.494 Y105.377 E.02698
G1 X118.974 Y108.728 E.1123
G1 X118.974 Y119.575 E.3598
G1 X118.465 Y121.118 E.05391
G1 X110.527 Y121.118 E.26331
G1 X110.527 Y109.296 E.39216
G2 X113.001 Y104.629 I-1.058 J-3.55 E.19505
M204 S250
G1 X112.389 Y104.18 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.718 Y104.18 E.19448
G1 X118.882 Y105.322 E.03543
G1 X119.366 Y108.7 E.10488
G1 X119.366 Y119.638 E.33608
G1 X118.748 Y121.51 E.06058
G1 X110.135 Y121.51 E.26466
G1 X110.135 Y108.991 E.38468
G2 X112.417 Y104.233 I-.668 J-3.246 E.18751
; WIPE_START
M204 S6000
G1 X114.416 Y104.216 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.104 Y106.549 Z5 F42000
G1 Z4.6
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.665 Y106.549 E.01859
G1 X116.816 Y107.606 E.03543
G2 X116.546 Y108.607 I1.257 J.876 E.03508
G2 X116.998 Y109.053 I.903 J-.461 E.02143
G1 X116.998 Y111.543 E.08257
G2 X116.546 Y112.8 I1.212 J1.145 E.04558
G2 X116.998 Y113.246 I.903 J-.461 E.02143
G1 X116.998 Y115.736 E.08257
G2 X116.546 Y116.993 I1.212 J1.145 E.04558
G2 X116.998 Y117.44 I.903 J-.46 E.02143
G1 X116.998 Y118.566 E.03737
G1 X116.895 Y118.638 E.00417
G1 X116.531 Y118.638 E.01206
M204 S10000
G1 X113.232 Y119.064 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X116.86 Y119.064 E.13141
M204 S10000
G1 X113.232 Y119.064 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X113.082 Y118.992 E.0059
; LINE_WIDTH: 0.433536
G1 F9216.216
G1 X112.946 Y118.783 E.00794
G1 X112.944 Y118.749 E.00108
G1 X112.944 Y110.305 E.26878
G1 X112.554 Y110.573 E.01508
G1 X112.56 Y119.085 E.27093
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X113.172 Y119.066 E.02112
M204 S10000
G1 X113.343 Y112.045 F42000
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X113.343 Y113.674 E.05401
G3 X113.792 Y114.634 I-1.077 J1.09 E.03592
G3 X113.343 Y115.326 I-.796 J-.026 E.02876
G1 X113.343 Y117.867 E.08429
G3 X113.742 Y118.638 I-.846 J.926 E.02942
G1 X115.511 Y118.638 E.05869
G2 X115.889 Y117.779 I-.976 J-.942 E.0318
G2 X115.674 Y117.255 I-.537 J-.086 E.01976
G3 X114.427 Y115.682 I.922 J-2.012 E.06909
G3 X114.642 Y115.158 I.537 J-.086 E.01976
G2 X115.889 Y113.586 I-.922 J-2.012 E.06909
G2 X115.674 Y113.062 I-.537 J-.086 E.01976
G3 X114.427 Y111.489 I.922 J-2.012 E.06909
G3 X114.642 Y110.965 I.537 J-.086 E.01976
G2 X115.889 Y109.393 I-.922 J-2.012 E.06909
G2 X115.674 Y108.869 I-.537 J-.086 E.01976
G1 X114.939 Y108.344 E.02995
G1 X114.686 Y107.987 E.01452
G3 X113.517 Y109.727 I-7.063 J-3.484 E.06973
G3 X113.792 Y110.441 I-.83 J.73 E.02592
G3 X113.343 Y111.133 I-.796 J-.026 E.02876
G1 X113.378 Y109.875 E.04174
; CHANGE_LAYER
; Z_HEIGHT: 4.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8843.478
G1 X113.343 Y111.133 E-.47813
G1 X113.578 Y110.965 E-.10962
G1 X113.77 Y110.703 E-.12349
G1 X113.781 Y110.575 E-.04876
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 24/79
; update layer progress
M73 L24
M991 S0 P23 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z5 I.857 J-.864 P1  F42000
G1 X61.516 Y58.759 Z5
G1 Z4.8
G1 E.8 F1800
; FEATURE: Inner wall
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z5.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z5.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z5.2 F4000
            G39.3 S1
            G0 Z5.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z4.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z5.2 F42000
G1 X116.734 Y101.741 Z5.2
G1 Z4.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
M73 P67 R7
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z5.2 F42000
G1 Z4.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.794 Y70.583 Z5.2 F42000
G1 X114.766 Y106.396 Z5.2
G1 Z4.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.995 Y106.396 E.07392
G1 X117.384 Y109.108 E.0909
G1 X117.384 Y119.198 E.33471
G1 X117.316 Y119.405 E.00722
G1 X112.307 Y119.405 E.16613
G1 X112.307 Y110.265 E.30319
G2 X114.759 Y106.455 I-2.865 J-4.537 E.15515
M204 S10000
G1 X114.394 Y105.988 F42000
G1 F8843.478
M204 S6000
G1 X117.348 Y105.988 E.09797
G1 X117.791 Y109.079 E.10357
G1 X117.791 Y119.264 E.33784
G1 X117.61 Y119.812 E.01915
G1 X111.9 Y119.812 E.1894
G1 X111.9 Y110.031 E.32445
G2 X114.39 Y106.048 I-2.485 J-4.324 E.16223
M204 S10000
G1 X113.989 Y105.581 F42000
G1 F8843.478
M204 S6000
G1 X117.7 Y105.581 E.12312
G1 X117.746 Y105.899 E.01066
G1 X118.198 Y109.05 E.10558
G1 X118.198 Y119.329 E.34098
M73 P68 R7
G1 X117.904 Y120.219 E.03108
G1 X111.493 Y120.219 E.21266
G1 X111.493 Y109.789 E.346
G2 X113.99 Y105.641 I-2.064 J-4.068 E.16927
M204 S10000
G1 X113.544 Y105.174 F42000
G1 F8843.478
M204 S6000
G1 X118.053 Y105.174 E.14958
G1 X118.149 Y105.842 E.02236
G1 X118.605 Y109.021 E.10654
G1 X118.605 Y119.395 E.34412
G1 X118.198 Y120.626 E.04302
G1 X111.086 Y120.626 E.23593
G1 X111.086 Y109.529 E.36812
G2 X113.552 Y105.234 I-1.613 J-3.781 E.17631
M204 S10000
G1 X113.049 Y104.767 F42000
G1 F8843.478
M204 S6000
G1 X118.406 Y104.767 E.17771
G1 X118.552 Y105.784 E.03407
G1 X119.012 Y108.992 E.10751
G1 X119.012 Y119.46 E.34725
G1 X118.493 Y121.033 E.05495
G1 X110.679 Y121.033 E.25919
G1 X110.679 Y109.252 E.39081
G2 X113.064 Y104.825 I-1.229 J-3.518 E.18307
M204 S250
G1 X112.484 Y104.375 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.746 Y104.375 E.19241
G1 X118.94 Y105.728 E.042
G1 X119.404 Y108.964 E.10044
G1 X119.404 Y119.523 E.32446
G1 X118.776 Y121.425 E.06155
G1 X110.287 Y121.425 E.26085
G1 X110.29 Y108.958 E.38308
G2 X112.509 Y104.43 I-.818 J-3.208 E.17613
; WIPE_START
M204 S6000
G1 X114.509 Y104.412 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X115.317 Y106.744 Z5.2 F42000
G1 Z4.8
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X115.055 Y106.744 E.00871
G3 X114.661 Y108.047 I-4.948 J-.783 E.04529
G2 X115.944 Y108.591 I1.316 J-1.317 E.04739
G1 X116.206 Y108.415 E.01047
G1 X116.809 Y107.555 E.03485
G1 X117.036 Y109.245 E.05655
G2 X116.206 Y109.322 I-.363 J.596 E.0296
G1 X115.682 Y110.123 E.03175
G3 X114.372 Y110.688 I-1.347 J-1.322 E.04854
G1 X114.11 Y110.512 E.01047
G1 X113.554 Y109.687 E.03301
G1 X113.483 Y109.763 E.00344
G1 X113.495 Y111.273 E.0501
G3 X114.11 Y111.418 I.189 J.572 E.02206
G1 X114.634 Y112.219 E.03175
G2 X115.944 Y112.784 I1.347 J-1.322 E.04854
G1 X116.206 Y112.609 E.01047
G1 X116.731 Y111.808 E.03175
G1 X117.036 Y111.577 E.01269
G1 X117.036 Y113.438 E.06173
G2 X116.206 Y113.515 I-.363 J.596 E.0296
G1 X115.682 Y114.316 E.03175
G3 X114.372 Y114.881 I-1.347 J-1.322 E.04854
G1 X114.11 Y114.705 E.01047
G1 X113.495 Y113.835 E.03533
G1 X113.495 Y115.466 E.05409
G3 X114.11 Y115.611 I.189 J.572 E.02206
G1 X114.634 Y116.412 E.03175
G2 X115.944 Y116.977 I1.347 J-1.322 E.04854
G1 X116.206 Y116.802 E.01047
G1 X116.731 Y116.001 E.03175
G1 X117.036 Y115.77 E.01269
G1 X117.036 Y117.631 E.06173
G2 X116.206 Y117.708 I-.363 J.596 E.0296
G1 X115.682 Y118.509 E.03175
G1 X114.066 Y118.553 E.05364
G2 X113.495 Y118.028 I-2.616 J2.272 E.02578
G1 X113.495 Y116.4 E.05401
M204 S10000
G1 X113.384 Y118.979 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X116.898 Y118.979 E.12728
M204 S10000
G1 X113.384 Y118.979 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X113.234 Y118.907 E.0059
; LINE_WIDTH: 0.433534
G1 F9216.263
G1 X113.098 Y118.698 E.00794
G1 X113.096 Y118.664 E.00108
G1 X113.096 Y110.166 E.27049
G1 X112.706 Y110.467 E.01568
G1 X112.712 Y119 E.27162
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X113.324 Y118.981 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 5
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X112.712 Y119 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 25/79
; update layer progress
M73 L25
M991 S0 P24 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z5.2 I.927 J-.788 P1  F42000
G1 X61.516 Y58.759 Z5.2
G1 Z5
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z5.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z5.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z5.4 F4000
            G39.3 S1
            G0 Z5.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z5
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z5.4 F42000
G1 X116.734 Y101.741 Z5.4
G1 Z5
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z5.4 F42000
G1 Z5
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.791 Y70.583 Z5.4 F42000
G1 X114.74 Y106.591 Z5.4
G1 Z5
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.023 Y106.591 E.07573
G1 X117.422 Y109.372 E.0932
G1 X117.422 Y119.084 E.32216
G1 X117.344 Y119.32 E.00826
G1 X112.459 Y119.32 E.16202
G1 X112.459 Y110.165 E.3037
G2 X114.73 Y106.65 I-3.022 J-4.443 E.14258
M204 S10000
G1 X114.377 Y106.184 F42000
G1 F8843.478
M204 S6000
G1 X117.376 Y106.184 E.09946
G1 X117.401 Y106.364 E.00604
G1 X117.829 Y109.343 E.09983
G1 X117.829 Y119.149 E.32529
G1 X117.638 Y119.727 E.02019
G1 X112.052 Y119.727 E.18529
G1 X112.052 Y109.942 E.32458
G2 X114.372 Y106.243 I-2.592 J-4.202 E.15002
M204 S10000
G1 X113.988 Y105.777 F42000
G1 F8843.478
M204 S6000
G1 X117.728 Y105.777 E.12406
G1 X117.804 Y106.306 E.01774
G1 X118.236 Y109.314 E.10079
G1 X118.236 Y119.215 E.32843
G1 X117.932 Y120.134 E.03212
G1 X111.645 Y120.134 E.20855
G1 X111.645 Y109.709 E.34583
G2 X113.988 Y105.837 I-2.163 J-3.953 E.15728
M204 S10000
G1 X113.572 Y105.37 F42000
G1 F8843.478
M204 S6000
G1 X118.081 Y105.37 E.1496
G1 X118.207 Y106.248 E.02945
G1 X118.643 Y109.285 E.10176
G1 X118.643 Y119.28 E.33156
G1 X118.226 Y120.541 E.04406
G1 X111.238 Y120.541 E.23182
G1 X111.238 Y109.458 E.36765
G2 X113.576 Y105.429 I-1.77 J-3.721 E.16422
M204 S10000
G1 X113.09 Y104.962 F42000
G1 F8843.478
M204 S6000
G1 X118.434 Y104.962 E.17727
G1 X118.61 Y106.191 E.04115
M73 P69 R7
G1 X119.05 Y109.256 E.10272
G1 X119.05 Y119.346 E.3347
G1 X118.521 Y120.948 E.05599
G1 X110.831 Y120.948 E.25508
G1 X110.831 Y109.193 E.38996
G2 X113.102 Y105.021 I-1.361 J-3.445 E.17104
M204 S250
G1 X112.567 Y104.57 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.774 Y104.57 E.19073
G1 X118.998 Y106.135 E.04856
G1 X119.442 Y109.228 E.09601
G1 X119.442 Y119.409 E.31283
G1 X118.804 Y121.34 E.06251
G1 X110.439 Y121.34 E.25704
G1 X110.439 Y108.913 E.38186
G2 X112.587 Y104.627 I-.967 J-3.166 E.16475
; WIPE_START
M204 S6000
G1 X114.587 Y104.608 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X115.412 Y106.939 Z5.4 F42000
G1 Z5
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X115.018 Y106.939 E.01308
G3 X114.634 Y108.109 I-8.987 J-2.3 E.04087
G2 X116.206 Y108.079 I.769 J-.902 E.05704
G1 X116.801 Y107.497 E.0276
G1 X117.068 Y109.36 E.06243
G1 X116.731 Y109.341 E.01122
G2 X115.682 Y110.205 I1.076 J2.374 E.04559
G3 X114.11 Y110.176 I-.769 J-.902 E.05704
G1 X113.647 Y109.692 E.02221
G1 X113.647 Y111.475 E.05913
G3 X114.634 Y112.302 I-1.038 J2.242 E.04322
G2 X116.206 Y112.272 I.769 J-.902 E.05704
G1 X116.731 Y111.725 E.02514
G1 X117.073 Y111.556 E.01268
G1 X117.073 Y113.553 E.06625
G1 X116.731 Y113.534 E.01139
G2 X115.682 Y114.398 I1.076 J2.374 E.04559
G3 X114.11 Y114.369 I-.769 J-.902 E.05704
G1 X113.647 Y113.885 E.02221
G1 X113.647 Y115.668 E.05913
G3 X114.634 Y116.495 I-1.038 J2.242 E.04322
G2 X116.206 Y116.465 I.769 J-.902 E.05704
G1 X116.731 Y115.918 E.02514
G1 X117.073 Y115.749 E.01268
G1 X117.073 Y117.746 E.06625
G1 X116.731 Y117.727 E.01139
G2 X115.8 Y118.469 I.907 J2.094 E.03992
G1 X114.021 Y118.469 E.05903
G1 X113.647 Y118.078 E.01792
G1 X113.647 Y116.45 E.05401
M204 S10000
G1 X113.536 Y118.894 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X116.925 Y118.894 E.12274
M204 S10000
G1 X113.536 Y118.894 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X113.386 Y118.822 E.0059
; LINE_WIDTH: 0.433532
G1 F9216.307
G1 X113.25 Y118.613 E.00794
G1 X113.248 Y118.579 E.00108
G1 X113.248 Y110.032 E.27205
G1 X112.858 Y110.36 E.01623
G1 X112.864 Y118.916 E.27231
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X113.476 Y118.896 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 5.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X112.864 Y118.916 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 26/79
; update layer progress
M73 L26
M991 S0 P25 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z5.4 I.926 J-.79 P1  F42000
G1 X61.516 Y58.759 Z5.4
G1 Z5.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z5.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z5.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z5.6 F4000
            G39.3 S1
            G0 Z5.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z5.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z5.6 F42000
G1 X116.734 Y101.741 Z5.6
G1 Z5.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z5.6 F42000
G1 Z5.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.786 Y70.582 Z5.6 F42000
G1 X114.699 Y106.786 Z5.6
G1 Z5.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.051 Y106.786 E.07799
G1 X117.46 Y109.636 E.0955
G1 X117.46 Y118.969 E.30961
G1 X117.372 Y119.235 E.0093
G1 X112.611 Y119.235 E.15791
G1 X112.611 Y110.056 E.30449
G2 X114.688 Y106.845 I-3.136 J-4.304 E.12975
M204 S10000
G1 X114.356 Y106.379 F42000
G1 F8843.478
M204 S6000
G1 X117.404 Y106.379 E.1011
G1 X117.46 Y106.771 E.01313
G1 X117.867 Y109.607 E.09504
G1 X117.867 Y119.035 E.31274
G1 X117.666 Y119.642 E.02123
G1 X112.204 Y119.642 E.18117
G1 X112.204 Y109.847 E.32494
G2 X114.348 Y106.438 I-2.721 J-4.09 E.13762
M204 S10000
G1 X113.986 Y105.972 F42000
G1 F8843.478
M204 S6000
G1 X117.756 Y105.972 E.12508
G1 X117.863 Y106.713 E.02483
G1 X118.274 Y109.578 E.096
G1 X118.274 Y119.1 E.31588
G1 X117.96 Y120.049 E.03316
G1 X111.797 Y120.049 E.20444
G1 X111.797 Y109.62 E.34596
G2 X113.982 Y106.032 I-2.316 J-3.87 E.14498
M204 S10000
G1 X113.583 Y105.565 F42000
G1 F8843.478
M204 S6000
G1 X118.109 Y105.565 E.15015
G1 X118.266 Y106.655 E.03653
G1 X118.681 Y109.549 E.09697
G1 X118.681 Y119.166 E.31901
G1 X118.254 Y120.456 E.0451
G1 X111.39 Y120.456 E.2277
G1 X111.39 Y109.387 E.3672
G2 X113.585 Y105.625 I-1.946 J-3.656 E.15213
M204 S10000
G1 X113.134 Y105.158 F42000
G1 F8843.478
M204 S6000
G1 X118.462 Y105.158 E.17674
G1 X118.669 Y106.597 E.04824
G1 X119.088 Y109.519 E.09793
G1 X119.088 Y119.231 E.32215
G1 X118.549 Y120.864 E.05703
G1 X110.983 Y120.864 E.25097
G1 X110.983 Y109.129 E.38927
G2 X113.143 Y105.217 I-1.545 J-3.405 E.15886
M204 S250
G1 X112.634 Y104.766 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.802 Y104.766 E.18953
G1 X119.057 Y106.542 E.05513
G1 X119.48 Y109.492 E.09157
G1 X119.48 Y119.294 E.3012
G1 X118.832 Y121.256 E.06347
G1 X110.591 Y121.256 E.25323
G1 X110.591 Y108.865 E.38073
G2 X112.651 Y104.823 I-1.122 J-3.118 E.15353
; WIPE_START
M204 S6000
G1 X114.651 Y104.804 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X115.407 Y107.134 Z5.6 F42000
G1 Z5.2
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
M73 P70 R7
G1 X116.749 Y107.134 E.04452
G1 X116.789 Y107.417 E.00949
G1 X116.206 Y107.862 E.02432
G3 X114.634 Y108.208 I-1.026 J-.914 E.05706
G1 X114.599 Y108.179 E.00152
G3 X113.763 Y109.468 I-7.322 J-3.832 E.05105
G1 X113.799 Y109.704 E.00791
G1 X114.11 Y109.958 E.01333
G2 X115.682 Y110.304 I1.026 J-.914 E.05706
G3 X116.731 Y109.482 I10.46 J12.249 E.04422
G1 X117.077 Y109.422 E.01166
G1 X117.111 Y111.048 E.05394
M204 S10000
G1 X113.799 Y113.367 F42000
G1 F8843.478
M204 S6000
G1 X113.799 Y111.738 E.05401
G3 X114.634 Y112.401 I-7.589 J10.423 E.03537
G2 X116.206 Y112.055 I.547 J-1.26 E.05706
G1 X116.731 Y111.626 E.02246
G1 X117.111 Y111.526 E.01306
G1 X117.111 Y113.61 E.06911
G1 X116.731 Y113.675 E.01281
G2 X115.682 Y114.497 I9.417 J13.079 E.04422
G3 X114.11 Y114.151 I-.547 J-1.26 E.05706
G1 X113.799 Y113.897 E.01333
G1 X113.799 Y115.931 E.06749
G3 X114.634 Y116.594 I-7.582 J10.415 E.03537
G2 X116.206 Y116.248 I.547 J-1.26 E.05706
G1 X116.731 Y115.819 E.02246
G1 X117.111 Y115.719 E.01306
G1 X117.111 Y117.803 E.06911
G1 X116.731 Y117.868 E.01281
G2 X116.057 Y118.384 I5.896 J8.393 E.02815
G1 X114.162 Y118.384 E.06285
G3 X113.799 Y118.09 I3.371 J-4.54 E.01551
G1 X113.799 Y116.462 E.05401
M204 S10000
G1 X113.688 Y118.81 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48738
G1 F8099.717
M204 S6000
G1 X116.958 Y118.81 E.11842
M204 S10000
G1 X113.688 Y118.81 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X113.538 Y118.737 E.0059
; LINE_WIDTH: 0.433531
G1 F9216.349
G1 X113.402 Y118.529 E.00794
G1 X113.4 Y118.495 E.00108
G1 X113.4 Y109.901 E.27353
G1 X113.01 Y110.243 E.01652
G1 X113.016 Y118.831 E.27333
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X113.628 Y118.811 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 5.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X113.016 Y118.831 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 27/79
; update layer progress
M73 L27
M991 S0 P26 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z5.6 I.924 J-.792 P1  F42000
G1 X61.516 Y58.759 Z5.6
G1 Z5.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z5.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z5.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z5.8 F4000
            G39.3 S1
            G0 Z5.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z5.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z5.8 F42000
G1 X116.734 Y101.741 Z5.8
G1 Z5.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z5.8 F42000
G1 Z5.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.781 Y70.582 Z5.8 F42000
G1 X114.659 Y106.981 Z5.8
G1 Z5.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.079 Y106.981 E.08027
G1 X117.115 Y107.235 E.00851
G1 X117.497 Y109.9 E.08929
G1 X117.497 Y118.855 E.29705
G1 X117.4 Y119.15 E.01034
G1 X112.763 Y119.15 E.15379
G1 X112.763 Y109.948 E.30525
G2 X114.645 Y107.039 I-3.346 J-4.227 E.11699
M204 S10000
G1 X114.328 Y106.574 F42000
G1 F8843.478
M204 S6000
G1 X117.432 Y106.574 E.10296
G1 X117.518 Y107.177 E.02021
G1 X117.904 Y109.87 E.09025
G1 X117.904 Y118.92 E.30019
G1 X117.694 Y119.558 E.02227
G1 X112.356 Y119.558 E.17706
G1 X112.356 Y109.738 E.32573
G2 X114.317 Y106.633 I-2.897 J-4.001 E.12482
M204 S10000
G1 X113.97 Y106.167 F42000
G1 F8843.478
M204 S6000
G1 X117.784 Y106.167 E.12652
G1 X117.921 Y107.119 E.03192
G1 X118.312 Y109.841 E.09122
G1 X118.312 Y118.985 E.30333
G1 X117.988 Y119.965 E.0342
G1 X111.949 Y119.965 E.20032
G1 X111.949 Y109.529 E.34618
G2 X113.964 Y106.227 I-2.557 J-3.826 E.13243
M204 S10000
G1 X113.582 Y105.76 F42000
G1 F8843.478
M204 S6000
G1 X118.137 Y105.76 E.15111
G1 X118.324 Y107.062 E.04362
G1 X118.719 Y109.812 E.09218
G1 X118.719 Y119.051 E.30646
G1 X118.282 Y120.372 E.04614
G1 X111.542 Y120.372 E.22359
G1 X111.542 Y109.298 E.36734
G2 X113.581 Y105.82 I-2.058 J-3.543 E.13982
M204 S10000
G1 X113.154 Y105.353 F42000
G1 F8843.478
M204 S6000
G1 X118.49 Y105.353 E.17701
G1 X118.727 Y107.004 E.05533
G1 X119.126 Y109.783 E.09314
G1 X119.126 Y119.116 E.3096
G1 X118.577 Y120.779 E.05807
G1 X111.135 Y120.779 E.24685
G1 X111.135 Y109.057 E.38885
G2 X113.16 Y105.413 I-1.684 J-3.32 E.14677
M204 S250
G1 X112.689 Y104.961 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.83 Y104.961 E.1887
G1 X119.115 Y106.948 E.06169
G1 X119.518 Y109.755 E.08714
G1 X119.518 Y119.179 E.28958
G1 X118.86 Y121.171 E.06444
G1 X110.743 Y121.171 E.24942
G1 X110.743 Y108.806 E.37994
G2 X112.703 Y105.019 I-1.268 J-3.057 E.14236
; WIPE_START
M204 S6000
G1 X114.703 Y105 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X115.07 Y107.329 Z5.8 F42000
G1 Z5.4
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.698 Y107.329 E.05401
G1 X116.206 Y107.657 E.0196
G3 X114.634 Y108.333 I-1.347 J-.966 E.05966
G1 X114.552 Y108.279 E.00325
G3 X113.905 Y109.306 I-13.417 J-7.734 E.04031
G1 X113.951 Y109.324 E.00163
G1 X113.951 Y109.648 E.01074
G1 X114.11 Y109.753 E.00634
G2 X115.682 Y110.429 I1.347 J-.966 E.05966
G2 X116.731 Y109.59 I-2.005 J-3.578 E.04475
G1 X117.081 Y109.452 E.01251
G1 X117.149 Y109.924 E.01585
G1 X117.149 Y111.484 E.05173
G1 X116.731 Y111.501 E.0139
G1 X116.206 Y111.85 E.02089
G3 X114.634 Y112.526 I-1.347 J-.966 E.05966
G3 X113.951 Y112.028 I1.159 J-2.307 E.02817
G1 X113.951 Y113.841 E.06013
G1 X114.11 Y113.947 E.00634
G2 X115.682 Y114.622 I1.347 J-.966 E.05966
G2 X116.731 Y113.783 I-2.005 J-3.578 E.04475
G1 X117.149 Y113.618 E.01492
M73 P71 R7
G1 X117.149 Y115.677 E.06831
G1 X116.731 Y115.694 E.0139
G1 X116.206 Y116.043 E.02089
G3 X114.634 Y116.719 I-1.347 J-.966 E.05966
G3 X113.951 Y116.221 I1.158 J-2.307 E.02817
G1 X113.951 Y118.034 E.06013
G3 X114.28 Y118.299 I-.635 J1.125 E.01409
G1 X116.385 Y118.299 E.06983
G3 X117.149 Y117.811 I.999 J.722 E.03079
G1 X117.149 Y116.183 E.05401
M204 S10000
G1 X113.84 Y118.725 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X117.012 Y118.725 E.11487
M204 S10000
G1 X113.84 Y118.725 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X113.69 Y118.653 E.0059
; LINE_WIDTH: 0.433529
G1 F9216.393
G1 X113.554 Y118.444 E.00794
G1 X113.552 Y118.41 E.00108
G1 X113.552 Y109.769 E.27503
G1 X113.162 Y110.127 E.01686
G1 X113.168 Y118.746 E.27433
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X113.78 Y118.727 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 5.6
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X113.168 Y118.746 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 28/79
; update layer progress
M73 L28
M991 S0 P27 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z5.8 I.922 J-.794 P1  F42000
G1 X61.516 Y58.759 Z5.8
G1 Z5.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z6 F4000
            G39.3 S1
            G0 Z6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z5.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z6 F42000
G1 X116.734 Y101.741 Z6
G1 Z5.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z6 F42000
G1 Z5.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.775 Y70.582 Z6 F42000
G1 X114.611 Y107.176 Z6
G1 Z5.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.107 Y107.176 E.08279
G1 X117.173 Y107.642 E.01559
G1 X117.535 Y110.163 E.0845
G1 X117.535 Y118.74 E.2845
G1 X117.428 Y119.066 E.01138
G1 X112.915 Y119.066 E.14968
G1 X112.915 Y109.817 E.3068
G2 X114.594 Y107.234 I-3.476 J-4.097 E.10365
M204 S10000
G1 X114.289 Y106.769 F42000
G1 F8843.478
M204 S6000
G1 X117.46 Y106.769 E.10517
G1 X117.576 Y107.584 E.0273
G1 X117.942 Y110.134 E.08547
G1 X117.942 Y118.805 E.28764
G1 X117.722 Y119.473 E.02331
G1 X112.508 Y119.473 E.17295
G1 X112.508 Y109.63 E.3265
G2 X114.276 Y106.828 I-3.044 J-3.879 E.11209
M204 S10000
G1 X113.953 Y106.362 F42000
G1 F8843.478
M204 S6000
G1 X117.812 Y106.362 E.12804
G1 X117.979 Y107.526 E.039
G1 X118.349 Y110.105 E.08643
G1 X118.349 Y118.871 E.29077
G1 X118.016 Y119.88 E.03525
G1 X112.101 Y119.88 E.19621
G1 X112.101 Y109.42 E.34696
G2 X113.944 Y106.422 I-2.636 J-3.685 E.11991
M204 S10000
G1 X113.579 Y105.955 F42000
G1 F8843.478
M204 S6000
G1 X118.165 Y105.955 E.15214
G1 X118.382 Y107.468 E.05071
G1 X118.756 Y110.076 E.08739
G1 X118.756 Y118.936 E.29391
G1 X118.31 Y120.287 E.04718
G1 X111.694 Y120.287 E.21948
G1 X111.694 Y109.211 E.36742
G2 X113.575 Y106.015 I-2.286 J-3.497 E.12745
M204 S10000
G1 X113.171 Y105.548 F42000
G1 F8843.478
M204 S6000
G1 X118.518 Y105.548 E.17738
G1 X118.785 Y107.411 E.06241
G1 X119.163 Y110.047 E.08835
G1 X119.163 Y119.002 E.29705
G1 X118.605 Y120.694 E.05911
G1 X111.287 Y120.694 E.24274
G1 X111.287 Y108.976 E.38871
G2 X113.173 Y105.608 I-1.821 J-3.232 E.13467
M204 S250
G1 X112.731 Y105.156 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.858 Y105.156 E.18827
G1 X119.173 Y107.355 E.06826
G1 X119.556 Y110.019 E.0827
G1 X119.556 Y119.065 E.27795
G1 X118.888 Y121.086 E.0654
G1 X110.895 Y121.086 E.24561
G1 X110.895 Y108.736 E.37949
G2 X112.741 Y105.215 I-1.415 J-2.986 E.13106
; WIPE_START
M204 S6000
G1 X114.741 Y105.196 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.936 Y108.442 Z6 F42000
G1 Z5.6
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.805 Y107.525 E.03075
G1 X116.104 Y107.525 E.02326
G3 X114.461 Y108.468 I-1.543 J-.783 E.06651
G3 X114.037 Y109.126 I-3.701 J-1.917 E.02599
G1 X114.103 Y109.151 E.00233
G1 X114.103 Y109.485 E.01108
G1 X114.634 Y110.155 E.02836
G2 X115.944 Y110.548 I1.059 J-1.151 E.04697
G2 X116.731 Y109.678 I-1.396 J-2.052 E.03927
G1 X117.082 Y109.453 E.01383
G3 X117.187 Y111.425 I-6.82 J1.353 E.06572
G2 X116.206 Y111.587 I-.382 J.734 E.03536
G3 X114.634 Y112.694 I-1.853 J-.962 E.06629
G3 X114.103 Y112.431 I.145 J-.959 E.01999
G1 X114.103 Y113.678 E.04139
G1 X114.634 Y114.348 E.02836
G2 X115.944 Y114.741 I1.059 J-1.151 E.04697
G2 X116.731 Y113.871 I-1.396 J-2.052 E.03927
G1 X117.187 Y113.579 E.01799
G1 X117.187 Y115.618 E.06765
G2 X116.206 Y115.78 I-.382 J.734 E.03536
G3 X114.634 Y116.887 I-1.853 J-.962 E.06629
G3 X114.103 Y116.624 I.145 J-.959 E.01999
G1 X114.103 Y117.871 E.04139
G3 X114.376 Y118.214 I-.569 J.733 E.01467
G1 X116.613 Y118.214 E.07419
G3 X117.187 Y117.772 I.927 J.61 E.0245
M73 P71 R6
G1 X117.187 Y116.143 E.05401
M204 S10000
G1 X113.992 Y118.64 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X117.049 Y118.64 E.11074
M204 S10000
G1 X113.992 Y118.64 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X113.842 Y118.568 E.0059
; LINE_WIDTH: 0.433525
G1 F9216.48
G1 X113.706 Y118.359 E.00794
G1 X113.704 Y118.325 E.00108
G1 X113.704 Y109.587 E.27813
G1 X113.314 Y109.985 E.01775
G1 X113.32 Y118.661 E.27615
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X113.932 Y118.642 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 5.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X113.32 Y118.661 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 29/79
; update layer progress
M73 L29
M991 S0 P28 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z6 I.92 J-.796 P1  F42000
G1 X61.516 Y58.759 Z6
G1 Z5.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z6.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z6.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z6.2 F4000
            G39.3 S1
            G0 Z6.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z5.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
M73 P72 R6
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z6.2 F42000
G1 X116.734 Y101.741 Z6.2
G1 Z5.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z6.2 F42000
G1 Z5.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.766 Y70.581 Z6.2 F42000
G1 X114.55 Y107.372 Z6.2
G1 Z5.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.135 Y107.372 E.08574
G1 X117.232 Y108.048 E.02268
G1 X117.573 Y110.427 E.07971
G1 X117.573 Y118.625 E.27195
G1 X117.456 Y118.981 E.01242
G1 X113.067 Y118.981 E.14557
G1 X113.067 Y109.691 E.30816
G2 X114.531 Y107.429 I-3.636 J-3.958 E.09036
M204 S10000
G1 X114.25 Y106.964 F42000
G1 F8843.478
M204 S6000
G1 X117.488 Y106.964 E.10738
G1 X117.635 Y107.991 E.03439
G1 X117.98 Y110.398 E.08068
G1 X117.98 Y118.691 E.27509
G1 X117.75 Y119.388 E.02435
G1 X112.66 Y119.388 E.16883
G1 X112.66 Y109.499 E.32802
G2 X114.235 Y107.022 I-3.254 J-3.807 E.09882
M204 S10000
G1 X113.92 Y106.557 F42000
G1 F8843.478
M204 S6000
G1 X117.84 Y106.557 E.13006
G1 X118.038 Y107.933 E.04609
G1 X118.387 Y110.369 E.08164
G1 X118.387 Y118.756 E.27822
G1 X118.044 Y119.795 E.03629
G1 X112.253 Y119.795 E.1921
G1 X112.253 Y109.312 E.34774
G2 X113.908 Y106.616 I-2.82 J-3.588 E.10716
M204 S10000
G1 X113.565 Y106.15 F42000
G1 F8843.478
M204 S6000
G1 X118.193 Y106.15 E.15354
G1 X118.441 Y107.875 E.05779
G1 X118.794 Y110.34 E.0826
G1 X118.794 Y118.822 E.28136
G1 X118.338 Y120.202 E.04822
G1 X111.846 Y120.202 E.21536
G1 X111.846 Y109.102 E.3682
G2 X113.558 Y106.21 I-2.373 J-3.358 E.11486
M204 S10000
G1 X113.175 Y105.743 F42000
G1 F8843.478
M204 S6000
G1 X118.546 Y105.743 E.17815
G1 X118.844 Y107.817 E.0695
G1 X119.201 Y110.311 E.08357
G1 X119.201 Y118.887 E.28449
G1 X118.633 Y120.609 E.06015
G1 X111.439 Y120.609 E.23863
G1 X111.439 Y108.892 E.38866
G2 X113.175 Y105.803 I-1.99 J-3.151 E.1225
M204 S250
G1 X112.76 Y105.351 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.886 Y105.351 E.18822
G1 X119.232 Y107.762 E.07482
G1 X119.593 Y110.283 E.07827
G1 X119.593 Y118.95 E.26633
G1 X118.916 Y121.001 E.06637
G1 X111.047 Y121.001 E.2418
G1 X111.047 Y108.663 E.37913
G2 X112.767 Y105.411 I-1.601 J-2.928 E.11972
; WIPE_START
M204 S6000
G1 X114.767 Y105.391 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.92 Y108.329 Z6.2 F42000
G1 Z5.8
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.833 Y107.72 E.0204
G1 X115.82 Y107.72 E.03361
G1 X115.346 Y108.344 E.02601
G1 X114.409 Y108.869 E.03561
G1 X114.284 Y109.131 E.00962
G2 X114.971 Y110.441 I2.3 J-.37 E.04993
G1 X115.908 Y110.965 E.03561
G1 X116.032 Y111.227 E.00962
G3 X115.346 Y112.538 I-2.301 J-.37 E.04993
G1 X114.409 Y113.062 E.03561
G1 X114.284 Y113.324 E.00962
G2 X114.971 Y114.634 I2.3 J-.37 E.04993
G1 X115.908 Y115.158 E.03561
G1 X116.032 Y115.42 E.00962
G3 X115.346 Y116.731 I-2.301 J-.37 E.04993
G1 X114.409 Y117.255 E.03561
G2 X114.468 Y118.129 I.705 J.392 E.03074
G1 X116.777 Y118.129 E.07658
G3 X117.225 Y117.634 I2.028 J1.385 E.02222
G1 X117.225 Y115.561 E.06878
G1 X116.505 Y115.158 E.02735
G1 X116.381 Y114.896 E.00962
G3 X117.225 Y113.441 I2.44 J.443 E.05692
G1 X117.225 Y111.368 E.06878
G1 X116.505 Y110.965 E.02735
G1 X116.381 Y110.703 E.00962
G3 X117.072 Y109.388 I2.17 J.302 E.05027
G3 X117.225 Y111.006 I-5.561 J1.341 E.05407
M204 S10000
G1 X114.144 Y118.555 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.4874
G1 F8099.351
M204 S6000
G1 X117.087 Y118.555 E.1066
M204 S10000
G1 X114.144 Y118.555 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X113.994 Y118.483 E.0059
; LINE_WIDTH: 0.433522
G1 F9216.541
G1 X113.858 Y118.274 E.00794
G1 X113.856 Y118.24 E.00108
G1 X113.856 Y109.432 E.28035
G1 X113.466 Y109.853 E.01827
G1 X113.472 Y118.576 E.27766
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X114.084 Y118.557 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 6
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X113.472 Y118.576 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 30/79
; update layer progress
M73 L30
M991 S0 P29 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z6.2 I.919 J-.798 P1  F42000
G1 X61.516 Y58.759 Z6.2
G1 Z6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z6.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z6.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z6.4 F4000
            G39.3 S1
            G0 Z6.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z6.4 F42000
G1 X116.734 Y101.741 Z6.4
G1 Z6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z6.4 F42000
G1 Z6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.757 Y70.581 Z6.4 F42000
G1 X114.485 Y107.567 Z6.4
G1 Z6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.163 Y107.567 E.08884
G1 X117.29 Y108.455 E.02977
G1 X117.611 Y110.691 E.07493
G1 X117.611 Y118.511 E.2594
G1 X117.484 Y118.896 E.01346
G1 X113.219 Y118.896 E.14145
G1 X113.219 Y109.541 E.31032
G2 X114.464 Y107.623 I-3.806 J-3.832 E.07642
M204 S10000
G1 X114.193 Y107.16 F42000
G1 F8843.478
M204 S6000
G1 X117.516 Y107.16 E.11022
G1 X117.693 Y108.397 E.04147
G1 X118.018 Y110.662 E.07589
G1 X118.018 Y118.576 E.26253
G1 X117.778 Y119.303 E.0254
G1 X112.812 Y119.303 E.16472
G1 X112.812 Y109.371 E.32947
G2 X114.175 Y107.217 I-3.442 J-3.686 E.08548
M204 S10000
G1 X113.877 Y106.753 F42000
G1 F8843.478
M204 S6000
G1 X117.868 Y106.753 E.13239
G1 X118.096 Y108.339 E.05318
G1 X118.425 Y110.633 E.07685
G1 X118.425 Y118.642 E.26567
G1 X118.072 Y119.71 E.03733
G1 X112.405 Y119.71 E.18798
G1 X112.405 Y109.182 E.34924
G2 X113.864 Y106.811 I-2.901 J-3.419 E.0939
M204 S10000
M73 P73 R6
G1 X113.543 Y106.346 F42000
G1 F8843.478
M204 S6000
G1 X118.221 Y106.346 E.15519
G1 X118.499 Y108.282 E.06488
G1 X118.832 Y110.604 E.07782
G1 X118.832 Y118.707 E.26881
G1 X118.366 Y120.117 E.04926
G1 X111.998 Y120.117 E.21125
G1 X111.998 Y108.994 E.36897
G2 X113.533 Y106.405 I-2.561 J-3.268 E.10219
M204 S10000
G1 X113.172 Y105.938 F42000
G1 F8843.478
M204 S6000
G1 X118.574 Y105.938 E.1792
G1 X118.902 Y108.224 E.07659
G1 X119.239 Y110.575 E.07878
G1 X119.239 Y118.773 E.27194
G1 X118.661 Y120.524 E.06119
G1 X111.591 Y120.524 E.23451
G1 X111.591 Y108.784 E.38944
G2 X113.168 Y105.998 I-2.166 J-3.065 E.10971
M204 S250
G1 X112.778 Y105.546 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.914 Y105.546 E.18853
G1 X119.29 Y108.168 E.08138
G1 X119.631 Y110.547 E.07383
G1 X119.631 Y118.836 E.2547
G1 X118.944 Y120.916 E.06733
G1 X111.199 Y120.916 E.23799
G1 X111.199 Y108.573 E.37928
G2 X112.781 Y105.606 I-1.732 J-2.829 E.10834
; WIPE_START
M204 S6000
G1 X114.781 Y105.587 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.408 Y108.97 Z6.4 F42000
G1 Z6
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X114.779 Y108.97 E.05401
G1 X114.542 Y109.393 E.01608
G2 X114.891 Y110.441 I1.447 J.101 E.0376
G3 X115.774 Y111.489 I-1.082 J1.809 E.04632
G3 X115.425 Y112.538 I-1.447 J.101 E.0376
G2 X114.542 Y113.586 I1.082 J1.809 E.04632
G2 X114.891 Y114.634 I1.447 J.101 E.0376
G3 X115.774 Y115.682 I-1.082 J1.809 E.04632
G3 X115.425 Y116.731 I-1.447 J.101 E.0376
G2 X114.542 Y117.779 I1.082 J1.809 E.04632
G1 X114.572 Y118.045 E.00887
G1 X116.841 Y118.045 E.07525
G3 X117.263 Y117.534 I.935 J.342 E.0224
G1 X117.263 Y115.451 E.06908
G3 X116.638 Y114.634 I.876 J-1.316 E.03475
G3 X117.263 Y113.341 I1.695 J.021 E.04919
G1 X117.263 Y111.258 E.06908
G3 X116.638 Y110.441 I.876 J-1.316 E.03475
G3 X116.987 Y109.393 I1.447 J-.101 E.0376
G1 X117.063 Y109.325 E.00337
G1 X117.263 Y110.939 E.05395
M204 S10000
G1 X114.296 Y118.47 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.116 Y118.47 E.10213
M204 S10000
G1 X114.296 Y118.47 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X114.146 Y118.398 E.0059
; LINE_WIDTH: 0.433519
G1 F9216.628
G1 X114.01 Y118.189 E.00794
G1 X114.008 Y118.155 E.00108
G1 X114.008 Y109.252 E.28338
G3 X113.618 Y109.695 I-11.67 J-9.879 E.0188
G1 X113.624 Y118.492 E.27997
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X114.236 Y118.472 E.02112
M204 S10000
G1 X114.538 Y108.518 F42000
; LINE_WIDTH: 0.541155
G1 F7225.507
M204 S6000
G1 X116.842 Y108.518 E.09353
G1 X116.77 Y108.019 E.02044
G1 X114.788 Y108.019 E.08049
G1 X114.565 Y108.464 E.02019
; CHANGE_LAYER
; Z_HEIGHT: 6.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F7225.507
G1 X114.788 Y108.019 E-.18895
G1 X116.29 Y108.019 E-.57105
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 31/79
; update layer progress
M73 L31
M991 S0 P30 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z6.4 I.814 J-.905 P1  F42000
G1 X61.516 Y58.759 Z6.4
G1 Z6.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z6.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z6.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z6.6 F4000
            G39.3 S1
            G0 Z6.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z6.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z6.6 F42000
G1 X116.734 Y101.741 Z6.6
G1 Z6.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z6.6 F42000
G1 Z6.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.746 Y70.58 Z6.6 F42000
G1 X114.41 Y107.762 Z6.6
G1 Z6.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.191 Y107.762 E.09225
G1 X117.348 Y108.862 E.03685
G1 X117.649 Y110.955 E.07014
G1 X117.649 Y118.396 E.24685
G1 X117.512 Y118.811 E.0145
G1 X113.371 Y118.811 E.13734
G1 X113.371 Y109.388 E.3126
G2 X114.386 Y107.817 I-4.04 J-3.724 E.06233
M204 S10000
G1 X114.127 Y107.355 F42000
G1 F8843.478
M204 S6000
G1 X117.544 Y107.355 E.11334
G1 X117.751 Y108.804 E.04856
G1 X118.056 Y110.926 E.0711
G1 X118.056 Y118.462 E.24998
G1 X117.806 Y119.218 E.02643
G1 X112.964 Y119.218 E.16061
G1 X112.964 Y109.221 E.33164
G2 X114.107 Y107.411 I-3.531 J-3.495 E.07154
M204 S10000
G1 X113.829 Y106.948 F42000
G1 F8843.478
M204 S6000
G1 X117.896 Y106.948 E.13492
G1 X118.154 Y108.746 E.06026
G1 X118.463 Y110.897 E.07206
G1 X118.463 Y118.527 E.25312
G1 X118.1 Y119.625 E.03837
G1 X112.557 Y119.625 E.18387
G1 X112.557 Y109.05 E.35079
G2 X113.813 Y107.005 I-3.114 J-3.32 E.08055
M204 S10000
G1 X113.509 Y106.541 F42000
G1 F8843.478
M204 S6000
G1 X118.249 Y106.541 E.15723
G1 X118.557 Y108.688 E.07197
G1 X118.87 Y110.867 E.07303
G1 X118.87 Y118.593 E.25626
G1 X118.394 Y120.032 E.0503
G1 X112.15 Y120.032 E.20714
G1 X112.15 Y108.865 E.37045
G2 X113.496 Y106.599 I-2.835 J-3.218 E.08886
M204 S10000
G1 X113.156 Y106.134 F42000
G1 F8843.478
M204 S6000
G1 X118.602 Y106.134 E.18067
G1 X118.96 Y108.631 E.08367
G1 X119.277 Y110.838 E.07399
G1 X119.277 Y118.658 E.25939
G1 X118.689 Y120.44 E.06223
M73 P74 R6
G1 X111.743 Y120.44 E.2304
G1 X111.743 Y108.677 E.3902
G2 X113.149 Y106.193 I-2.346 J-2.967 E.09706
M204 S250
G1 X112.784 Y105.742 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.942 Y105.742 E.18921
G1 X119.348 Y108.575 E.08795
G1 X119.669 Y110.81 E.0694
G1 X119.669 Y118.721 E.24307
G1 X118.972 Y120.832 E.06829
G1 X111.351 Y120.832 E.23418
G1 X111.351 Y108.473 E.37976
G2 X112.784 Y105.802 I-1.879 J-2.728 E.09674
; WIPE_START
M204 S6000
G1 X114.784 Y105.782 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.484 Y109.166 Z6.6 F42000
G1 Z6.2
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X114.855 Y109.166 E.05401
G1 X114.693 Y109.393 E.00927
G2 X115.249 Y110.965 I1.503 J.353 E.05844
G3 X115.52 Y112.538 I-.907 J.966 E.0568
G2 X114.693 Y113.586 I5.362 J5.082 E.04436
G2 X115.249 Y115.158 I1.503 J.353 E.05844
G3 X115.52 Y116.731 I-.907 J.966 E.0568
G2 X114.693 Y117.779 I5.362 J5.082 E.04436
G1 X114.671 Y117.96 E.00604
G1 X116.836 Y117.96 E.0718
G1 X116.893 Y117.779 E.00629
G1 X117.3 Y117.306 E.02069
G1 X117.3 Y115.316 E.06602
G1 X117.164 Y115.158 E.00692
G3 X117.3 Y113.113 I.909 J-.966 E.07768
G1 X117.3 Y111.123 E.06602
G3 X116.789 Y110.441 I3.502 J-3.158 E.02831
G3 X117.047 Y109.214 I1.348 J-.357 E.04314
G1 X117.278 Y110.826 E.05401
M204 S10000
G1 X114.448 Y118.386 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.144 Y118.386 E.09764
M204 S10000
G1 X114.448 Y118.386 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X114.298 Y118.313 E.0059
; LINE_WIDTH: 0.433696
G1 F9212.451
G1 X114.162 Y118.105 E.00794
G1 X114.16 Y118.071 E.00108
G1 X114.16 Y109.599 E.26978
; LINE_WIDTH: 0.431834
G1 F9256.564
G1 X114.17 Y109.055 E.01724
G1 X114.195 Y108.969 E.00283
G1 X113.812 Y109.478 E.0202
G1 X113.77 Y109.599 E.00404
G1 X113.776 Y118.407 E.27915
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X114.388 Y118.387 E.02112
M204 S10000
G1 X114.382 Y108.757 F42000
; LINE_WIDTH: 0.538065
G1 F7270.596
M204 S6000
G1 X114.839 Y108.713 E.01853
G1 X116.87 Y108.713 E.08196
G1 X116.798 Y108.215 E.02031
G1 X114.689 Y108.215 E.08512
G2 X114.41 Y108.704 I7.788 J4.765 E.02274
; CHANGE_LAYER
; Z_HEIGHT: 6.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F7270.596
G1 X114.689 Y108.215 E-.21415
G1 X116.125 Y108.215 E-.54585
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 32/79
; update layer progress
M73 L32
M991 S0 P31 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z6.6 I.817 J-.902 P1  F42000
G1 X61.516 Y58.759 Z6.6
G1 Z6.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z6.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z6.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z6.8 F4000
            G39.3 S1
            G0 Z6.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z6.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z6.8 F42000
G1 X116.734 Y101.741 Z6.8
G1 Z6.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z6.8 F42000
G1 Z6.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.735 Y70.579 Z6.8 F42000
G1 X114.329 Y107.957 Z6.8
G1 Z6.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.219 Y107.957 E.09586
G1 X117.407 Y109.268 E.04394
G1 X117.687 Y111.218 E.06535
G1 X117.687 Y118.282 E.2343
G1 X117.54 Y118.726 E.01554
G1 X113.523 Y118.726 E.13323
G1 X113.523 Y109.214 E.31555
G2 X114.304 Y108.012 I-3.996 J-3.448 E.04769
M204 S10000
G1 X114.058 Y107.55 F42000
G1 F8843.478
M204 S6000
G1 X117.572 Y107.55 E.11656
G1 X117.81 Y109.211 E.05564
G1 X118.094 Y111.189 E.06631
G1 X118.094 Y118.347 E.23743
G1 X117.834 Y119.134 E.02748
G1 X113.116 Y119.134 E.15649
G1 X113.116 Y109.063 E.33406
G2 X114.035 Y107.606 I-3.812 J-3.421 E.05742
M204 S10000
G1 X113.772 Y107.143 F42000
G1 F8843.478
M204 S6000
G1 X117.924 Y107.143 E.13775
G1 X118.213 Y109.153 E.06735
G1 X118.501 Y111.16 E.06728
G1 X118.501 Y118.412 E.24057
G1 X118.128 Y119.541 E.03941
G1 X112.709 Y119.541 E.17976
G1 X112.709 Y108.9 E.35297
G2 X113.753 Y107.2 I-3.242 J-3.16 E.06672
M204 S10000
G1 X113.468 Y106.736 F42000
G1 F8843.478
M204 S6000
G1 X118.277 Y106.736 E.15952
G1 X118.616 Y109.095 E.07905
G1 X118.908 Y111.131 E.06824
G1 X118.908 Y118.478 E.2437
G1 X118.422 Y119.948 E.05134
G1 X112.302 Y119.948 E.20302
G1 X112.302 Y108.728 E.37217
G2 X113.453 Y106.794 I-2.905 J-3.038 E.07559
M204 S10000
G1 X113.131 Y106.329 F42000
G1 F8843.478
M204 S6000
G1 X118.63 Y106.329 E.18241
G1 X119.019 Y109.037 E.09076
G1 X119.315 Y111.102 E.0692
G1 X119.315 Y118.543 E.24684
G1 X118.717 Y120.355 E.06327
G1 X111.895 Y120.355 E.22629
G1 X111.895 Y108.549 E.39162
G2 X113.121 Y106.388 I-2.551 J-2.874 E.08392
M204 S250
G1 X112.779 Y105.937 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.97 Y105.937 E.19023
G1 X119.407 Y108.982 E.09451
G1 X119.707 Y111.074 E.06496
G1 X119.707 Y118.606 E.23145
G1 X119 Y120.747 E.06926
G1 X111.503 Y120.747 E.23037
G1 X111.503 Y108.366 E.38043
G2 X112.774 Y105.997 I-2.092 J-2.649 E.08498
; WIPE_START
M204 S6000
G1 X114.774 Y105.977 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X114.727 Y113.61 Z6.8 F42000
G1 X114.711 Y116.31 Z6.8
G1 Z6.4
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X114.711 Y117.875 E.0519
G1 X114.775 Y117.875 E.00211
G1 X114.807 Y117.779 E.00337
G2 X115.637 Y116.731 I-4.233 J-4.205 E.04445
G2 X115.046 Y115.158 I-1.544 J-.317 E.05877
G1 X114.711 Y114.68 E.01938
M73 P75 R6
G1 X114.711 Y113.87 E.02687
G1 X114.807 Y113.586 E.00995
G2 X115.637 Y112.538 I-4.233 J-4.205 E.04445
G2 X115.046 Y110.965 I-1.544 J-.317 E.05877
G1 X114.711 Y110.487 E.01938
G1 X114.711 Y109.677 E.02687
G3 X114.835 Y109.361 I.44 J-.009 E.01157
G1 X116.775 Y109.393 E.06436
G2 X117.285 Y110.873 I1.474 J.32 E.0546
G1 X117.338 Y111.243 E.01242
G1 X117.338 Y112.84 E.05297
G2 X116.775 Y113.586 I3.025 J2.869 E.03105
G2 X117.338 Y115.126 I1.519 J.318 E.05731
G1 X117.338 Y117.033 E.06326
G2 X116.766 Y117.875 I2.144 J2.072 E.03392
G1 X115.138 Y117.875 E.05401
M204 S10000
G1 X114.6 Y118.301 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.172 Y118.301 E.09315
M204 S10000
G1 X114.6 Y108.951 F42000
; LINE_WIDTH: 0.477073
G1 F8292.017
M204 S6000
G1 X114.673 Y108.929 E.00269
; LINE_WIDTH: 0.540827
G1 F7230.271
G1 X114.746 Y108.908 E.00309
G1 X116.898 Y108.908 E.0873
G1 X116.826 Y108.41 E.02042
G1 X114.6 Y108.41 E.09031
; LINE_WIDTH: 0.51805
G1 F7576.874
G1 X114.511 Y108.522 E.00556
; LINE_WIDTH: 0.47183
G1 F8393.369
G1 X114.421 Y108.634 E.00502
; LINE_WIDTH: 0.42561
G1 F9407.092
G1 X114.332 Y108.747 E.00448
; LINE_WIDTH: 0.391399
G1 F10330.616
G2 X113.962 Y109.296 I2.429 J2.032 E.01884
; LINE_WIDTH: 0.433378
G1 F9219.942
G1 X113.922 Y109.415 E.00398
G1 X113.928 Y118.322 E.2834
; LINE_WIDTH: 0.468371
G1 F8461.615
G1 X114.6 Y118.301 E.02332
G1 X114.45 Y118.229 E.00577
; LINE_WIDTH: 0.43369
G1 F9212.592
G1 X114.314 Y118.02 E.00794
G1 X114.312 Y117.986 E.00108
G1 X114.312 Y109.415 E.27292
; LINE_WIDTH: 0.410618
G1 F9790.657
G1 X114.35 Y109.287 E.004
; LINE_WIDTH: 0.365533
G1 F11158.897
G1 X114.388 Y109.159 E.00351
; LINE_WIDTH: 0.361777
G1 F11290.339
G1 X114.445 Y109.103 E.00205
; LINE_WIDTH: 0.39935
G1 F10100.16
G1 X114.501 Y109.048 E.00229
; LINE_WIDTH: 0.436924
G1 F9136.979
G1 X114.557 Y108.993 E.00254
; CHANGE_LAYER
; Z_HEIGHT: 6.6
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9136.979
G1 X114.501 Y109.048 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 33/79
; update layer progress
M73 L33
M991 S0 P32 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z6.8 I.838 J-.883 P1  F42000
G1 X61.516 Y58.759 Z6.8
G1 Z6.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z7 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z7
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z7 F4000
            G39.3 S1
            G0 Z7 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z6.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z7 F42000
G1 X116.734 Y101.741 Z7
G1 Z6.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z7 F42000
G1 Z6.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.72 Y70.578 Z7 F42000
G1 X114.231 Y108.152 Z7
G1 Z6.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.247 Y108.152 E.10003
G1 X117.465 Y109.675 E.05103
G1 X117.724 Y111.482 E.06056
G1 X117.724 Y118.167 E.22174
G1 X117.568 Y118.642 E.01658
G1 X113.675 Y118.642 E.12911
G1 X113.675 Y109.033 E.31875
G2 X114.203 Y108.206 I-4.648 J-3.55 E.03259
M204 S10000
G1 X113.974 Y107.745 F42000
G1 F8843.478
M204 S6000
G1 X117.6 Y107.745 E.12027
G1 X117.868 Y109.617 E.06273
G1 X118.131 Y111.453 E.06152
G1 X118.131 Y118.232 E.22488
G1 X117.862 Y119.049 E.02852
G1 X113.268 Y119.049 E.15238
G1 X113.268 Y108.886 E.33712
G2 X113.949 Y107.8 I-3.932 J-3.221 E.04263
M204 S10000
G1 X113.706 Y107.338 F42000
G1 F8843.478
M204 S6000
G1 X117.952 Y107.338 E.14088
G1 X118.271 Y109.559 E.07444
G1 X118.539 Y111.424 E.06249
G1 X118.539 Y118.298 E.22802
G1 X118.156 Y119.456 E.04045
G1 X112.861 Y119.456 E.17564
G1 X112.861 Y108.734 E.35565
G2 X113.683 Y107.394 I-3.549 J-3.1 E.05241
M204 S10000
G1 X113.409 Y106.931 F42000
G1 F8843.478
M204 S6000
G1 X118.305 Y106.931 E.16243
G1 X118.674 Y109.502 E.08614
G1 X118.946 Y111.395 E.06345
G1 X118.946 Y118.363 E.23115
G1 X118.45 Y119.863 E.05238
G1 X112.454 Y119.863 E.19891
G1 X112.454 Y108.583 E.37418
G2 X113.391 Y106.988 I-3.031 J-2.853 E.06185
M204 S10000
G1 X113.094 Y106.524 F42000
G1 F8843.478
M204 S6000
G1 X118.658 Y106.524 E.18457
G1 X119.077 Y109.444 E.09784
G1 X119.353 Y111.366 E.06441
G1 X119.353 Y118.429 E.23429
G1 X118.745 Y120.27 E.06432
G1 X112.047 Y120.27 E.22217
G1 X112.047 Y108.41 E.39343
G2 X113.081 Y106.583 I-2.578 J-2.665 E.0706
M204 S250
G1 X112.762 Y106.132 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X118.998 Y106.132 E.19163
G1 X119.465 Y109.388 E.10108
G1 X119.745 Y111.338 E.06053
G1 X119.745 Y118.492 E.21982
G1 X119.028 Y120.662 E.07022
G1 X111.655 Y120.662 E.22656
G1 X111.655 Y108.238 E.38176
G2 X112.754 Y106.191 I-2.253 J-2.528 E.07285
; WIPE_START
M204 S6000
G1 X114.754 Y106.172 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X115.034 Y109.556 Z7 F42000
G1 Z6.6
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X114.863 Y109.556 E.00568
G1 X114.863 Y111.013 E.04833
G3 X115.793 Y112.538 I-.985 J1.647 E.06162
G1 X115.509 Y113.062 E.01977
G1 X114.863 Y113.649 E.02897
G1 X114.863 Y115.206 E.05164
G3 X115.793 Y116.731 I-.985 J1.647 E.06162
G1 X115.509 Y117.255 E.01977
G1 X114.893 Y117.79 E.02707
G1 X116.621 Y117.79 E.05733
G3 X117.376 Y116.848 I2.087 J.899 E.04052
G1 X117.376 Y114.961 E.06261
G3 X116.62 Y113.586 I1.025 J-1.459 E.0539
M73 P75 R5
G3 X117.376 Y112.655 I1.6 J.528 E.04067
G2 X117.255 Y110.664 I-7.002 J-.574 E.06641
G3 X116.643 Y109.556 I1.045 J-1.301 E.04307
G1 X115.034 Y109.556 E.05336
M204 S10000
G1 X114.752 Y118.216 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.2 Y118.216 E.08865
M204 S10000
G1 X114.709 Y109.105 F42000
; LINE_WIDTH: 0.541367
G1 F7222.435
M204 S6000
G1 X116.926 Y109.103 E.09005
G1 X116.854 Y108.605 E.02044
G2 X114.488 Y108.609 I-1.051 J80.376 E.0961
; LINE_WIDTH: 0.529313
G1 F7401.43
G1 X114.332 Y108.819 E.01036
; LINE_WIDTH: 0.481757
M73 P76 R5
G1 F8203.505
G2 X114.09 Y109.16 I2.789 J2.237 E.01497
; LINE_WIDTH: 0.433883
G1 F9208.041
G1 X114.074 Y109.445 E.0091
G1 X114.08 Y118.237 E.2801
; LINE_WIDTH: 0.468371
G1 F8461.615
G1 X114.752 Y118.216 E.02332
G1 X114.602 Y118.144 E.00577
; LINE_WIDTH: 0.434018
G1 F9204.872
G1 X114.466 Y117.935 E.00795
G1 X114.464 Y117.901 E.00108
G1 X114.464 Y109.445 E.26948
G1 X114.508 Y109.294 E.00502
; LINE_WIDTH: 0.4891
G1 F8068.493
G1 X114.587 Y109.22 E.00392
; LINE_WIDTH: 0.52632
G1 F7447.249
G1 X114.665 Y109.146 E.00424
; CHANGE_LAYER
; Z_HEIGHT: 6.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F7447.249
G1 X114.587 Y109.22 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 34/79
; update layer progress
M73 L34
M991 S0 P33 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z7 I.839 J-.882 P1  F42000
G1 X61.516 Y58.759 Z7
G1 Z6.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z7.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z7.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z7.2 F4000
            G39.3 S1
            G0 Z7.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z6.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z7.2 F42000
G1 X116.734 Y101.741 Z7.2
G1 Z6.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z7.2 F42000
G1 Z6.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.706 Y70.577 Z7.2 F42000
G1 X114.129 Y108.348 Z7.2
G1 Z6.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.275 Y108.348 E.10434
G1 X117.523 Y110.082 E.05811
G1 X117.762 Y111.746 E.05577
G1 X117.762 Y118.052 E.20919
G1 X117.596 Y118.557 E.01763
G1 X113.827 Y118.557 E.125
G1 X113.827 Y108.823 E.32288
G2 X114.101 Y108.4 I-2.588 J-1.976 E.01673
M204 S10000
G1 X113.88 Y107.94 F42000
G1 F8843.478
M204 S6000
G1 X117.628 Y107.94 E.1243
G1 X117.926 Y110.024 E.06982
G1 X118.169 Y111.717 E.05674
G1 X118.169 Y118.118 E.21233
G1 X117.89 Y118.964 E.02956
G1 X113.42 Y118.964 E.14827
G1 X113.42 Y108.691 E.34077
G2 X113.853 Y107.994 I-3.97 J-2.95 E.02725
M204 S10000
G1 X113.626 Y107.533 F42000
G1 F8843.478
M204 S6000
G1 X117.98 Y107.533 E.14445
G1 X118.329 Y109.966 E.08152
G1 X118.576 Y111.688 E.0577
G1 X118.576 Y118.183 E.21546
G1 X118.184 Y119.371 E.04149
G1 X113.013 Y119.371 E.17153
G1 X113.013 Y108.559 E.35865
G2 X113.601 Y107.588 I-4.03 J-3.102 E.03773
M204 S10000
G1 X113.345 Y107.126 F42000
G1 F8843.478
M204 S6000
G1 X118.333 Y107.126 E.16547
G1 X118.732 Y109.908 E.09323
G1 X118.983 Y111.659 E.05866
G1 X118.983 Y118.249 E.2186
G1 X118.478 Y119.778 E.05342
G1 X112.606 Y119.778 E.1948
G1 X112.606 Y108.407 E.3772
G2 X113.325 Y107.183 I-3.022 J-2.597 E.04734
M204 S10000
G1 X113.048 Y106.719 F42000
G1 F8843.478
M204 S6000
G1 X118.686 Y106.719 E.18704
G1 X119.135 Y109.851 E.10493
G1 X119.391 Y111.63 E.05963
G1 X119.391 Y118.314 E.22174
G1 X118.773 Y120.185 E.06536
G1 X112.199 Y120.185 E.21806
G1 X112.199 Y108.256 E.39572
G2 X113.031 Y106.777 I-2.825 J-2.563 E.05676
M204 S250
G1 X112.733 Y106.327 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X119.026 Y106.327 E.19337
G1 X119.523 Y109.795 E.10764
G1 X119.783 Y111.602 E.05609
G1 X119.783 Y118.377 E.20819
G1 X119.056 Y120.577 E.07119
G1 X111.807 Y120.577 E.22275
G1 X111.807 Y108.095 E.38353
G2 X112.721 Y106.386 I-2.435 J-2.402 E.06039
; WIPE_START
M204 S6000
G1 X114.721 Y106.367 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X114.949 Y113.996 Z7.2 F42000
G1 X115.015 Y116.186 Z7.2
G1 Z6.8
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X115.015 Y117.705 E.0504
G1 X115.124 Y117.705 E.00362
G1 X116.016 Y117.255 E.03317
G2 X115.338 Y115.682 I-1.863 J-.129 E.05902
G1 X115.015 Y115.519 E.012
G1 X115.015 Y113.567 E.06475
G1 X116.016 Y113.062 E.03722
G2 X115.338 Y111.489 I-1.863 J-.129 E.05902
G1 X115.015 Y111.326 E.012
G1 X115.015 Y109.751 E.05225
G1 X116.553 Y109.751 E.05101
G1 X116.623 Y109.917 E.00598
G2 X117.246 Y110.6 I3.386 J-2.46 E.03072
G3 X117.414 Y112.548 I-6.705 J1.559 E.06507
G1 X116.396 Y113.062 E.03782
G2 X117.075 Y114.634 I1.863 J.129 E.05902
G1 X117.414 Y114.949 E.01536
G1 X117.414 Y116.741 E.05943
G1 X116.396 Y117.255 E.03782
G1 X116.399 Y117.705 E.01495
G1 X117.414 Y117.705 E.03366
G1 X117.414 Y117.092 E.02035
M204 S10000
G1 X114.904 Y118.131 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.228 Y118.131 E.08416
M204 S10000
G1 X114.904 Y118.131 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X114.754 Y118.059 E.0059
; LINE_WIDTH: 0.433715
G1 F9212.009
G1 X114.618 Y117.85 E.00794
G1 X114.616 Y117.816 E.00108
G1 X114.616 Y109.64 E.26036
; LINE_WIDTH: 0.455204
G1 F8731.86
G1 X114.62 Y109.579 E.00207
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X114.623 Y109.517 E.00229
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X114.627 Y109.456 E.00251
; LINE_WIDTH: 0.573558
G1 F6784.295
G1 X114.743 Y109.325 E.00757
G1 X114.904 Y109.298 E.00707
; LINE_WIDTH: 0.541149
G1 F7225.595
G1 X116.954 Y109.298 E.08322
G1 X116.882 Y108.8 E.02044
G1 X114.904 Y108.8 E.08032
; LINE_WIDTH: 0.554223
G1 F7040.842
G1 X114.648 Y108.813 E.01067
; LINE_WIDTH: 0.583569
G1 F6658.667
G1 X114.392 Y108.826 E.01129
G1 X114.306 Y109.018 E.00926
G1 X114.292 Y109.317 E.01319
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X114.27 Y109.425 E.00449
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X114.248 Y109.533 E.00409
; LINE_WIDTH: 0.43367
G1 F9213.061
G1 X114.226 Y109.64 E.0035
G1 X114.232 Y118.152 E.27103
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X114.844 Y118.133 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 7
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X114.232 Y118.152 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 35/79
; update layer progress
M73 L35
M991 S0 P34 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z7.2 I.91 J-.808 P1  F42000
G1 X61.516 Y58.759 Z7.2
G1 Z7
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z7.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z7.4
M73 P77 R5
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z7.4 F4000
            G39.3 S1
            G0 Z7.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z7
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z7.4 F42000
G1 X116.734 Y101.741 Z7.4
G1 Z7
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z7.4 F42000
G1 Z7
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.683 Y70.576 Z7.4 F42000
G1 X113.979 Y108.543 Z7.4
G1 Z7
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.303 Y108.543 E.11024
G1 X117.582 Y110.488 E.0652
G1 X117.8 Y112.01 E.05099
G1 X117.8 Y117.938 E.19664
G1 X117.624 Y118.472 E.01867
G1 X113.979 Y118.472 E.12089
G1 X113.979 Y108.603 E.32738
M204 S10000
G1 X113.782 Y108.136 F42000
G1 F8843.478
M204 S6000
G1 X117.656 Y108.136 E.12849
G1 X117.985 Y110.431 E.0769
G1 X118.207 Y111.981 E.05195
G1 X118.207 Y118.003 E.19978
G1 X117.918 Y118.879 E.0306
G1 X113.572 Y118.879 E.14415
G1 X113.572 Y108.484 E.34483
G1 X113.751 Y108.187 E.01149
M204 S10000
G1 X113.531 Y107.729 F42000
G1 F8843.478
M204 S6000
G1 X118.008 Y107.729 E.14853
G1 X118.388 Y110.373 E.08861
G1 X118.614 Y111.952 E.05291
G1 X118.614 Y118.069 E.20291
G1 X118.212 Y119.286 E.04253
G1 X113.165 Y119.286 E.16742
G1 X113.165 Y108.35 E.36279
G2 X113.504 Y107.782 I-3.736 J-2.619 E.02194
M204 S10000
G1 X113.27 Y107.322 F42000
G1 F8843.478
M204 S6000
G1 X118.361 Y107.322 E.16887
G1 X118.791 Y110.315 E.10031
G1 X119.021 Y111.923 E.05387
G1 X119.021 Y118.134 E.20605
G1 X118.506 Y119.693 E.05447
G1 X112.758 Y119.693 E.19068
G1 X112.758 Y108.217 E.38067
G2 X113.248 Y107.377 I-3.002 J-2.311 E.03235
M204 S10000
G1 X112.989 Y106.914 F42000
G1 F8843.478
M204 S6000
G1 X118.714 Y106.914 E.18992
G1 X119.194 Y110.257 E.11202
G1 X119.428 Y111.894 E.05484
G1 X119.428 Y118.2 E.20919
G1 X118.801 Y120.1 E.0664
G1 X112.351 Y120.1 E.21395
G1 X112.351 Y108.079 E.39876
G2 X112.969 Y106.971 I-2.874 J-2.33 E.0423
M204 S250
G1 X112.692 Y106.522 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X119.054 Y106.522 E.19547
G1 X119.582 Y110.202 E.11421
G1 X119.82 Y111.866 E.05166
G1 X119.82 Y118.263 E.19657
G1 X119.084 Y120.492 E.07215
G1 X111.959 Y120.492 E.21894
G1 X111.959 Y107.934 E.38588
G2 X112.677 Y106.58 I-2.666 J-2.282 E.04747
; WIPE_START
M204 S6000
G1 X114.677 Y106.562 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X115.167 Y110.189 Z7.4 F42000
G1 Z7
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X115.167 Y109.946 E.00806
G1 X116.552 Y109.946 E.04595
G2 X117.227 Y110.469 I1.091 J-.713 E.02885
G1 X117.452 Y112.035 E.05248
G1 X117.452 Y112.455 E.01394
G3 X116.731 Y112.674 I-.62 J-.746 E.02568
G1 X116.206 Y112.406 E.01953
G2 X115.167 Y111.45 I-1.899 J1.023 E.04771
G1 X115.167 Y113.54 E.06932
G1 X115.682 Y113.449 E.01736
G1 X116.206 Y113.718 E.01953
G2 X117.255 Y114.679 I1.911 J-1.033 E.04806
G1 X117.452 Y114.709 E.00662
G1 X117.452 Y116.648 E.06432
G3 X116.731 Y116.867 I-.62 J-.746 E.02568
G1 X116.206 Y116.599 E.01953
G2 X115.167 Y115.643 I-1.899 J1.023 E.04771
G1 X115.167 Y117.271 E.05401
M204 S10000
G1 X115.056 Y118.046 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.256 Y118.046 E.07967
M204 S10000
G1 X115.056 Y118.046 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X114.906 Y117.974 E.0059
; LINE_WIDTH: 0.433734
G1 F9211.561
G1 X114.77 Y117.765 E.00794
G1 X114.768 Y117.731 E.00108
G1 X114.768 Y109.835 E.25145
; LINE_WIDTH: 0.455204
G1 F8731.86
G1 X114.772 Y109.774 E.00207
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X114.775 Y109.712 E.00229
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X114.779 Y109.651 E.00251
; LINE_WIDTH: 0.573558
G1 F6784.295
G1 X114.895 Y109.52 E.00757
G1 X115.056 Y109.494 E.00707
; LINE_WIDTH: 0.541149
G1 F7225.595
G1 X116.982 Y109.494 E.07818
G1 X116.91 Y108.995 E.02044
G1 X115.056 Y108.995 E.07528
; LINE_WIDTH: 0.554223
G1 F7040.842
G1 X114.757 Y109.008 E.01247
; LINE_WIDTH: 0.579768
G1 F6705.807
G1 X114.458 Y109.022 E.01309
G1 X114.444 Y109.512 E.02147
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X114.422 Y109.62 E.00449
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X114.4 Y109.728 E.00409
; LINE_WIDTH: 0.433687
G1 F9212.658
G1 X114.378 Y109.835 E.0035
G1 X114.384 Y118.068 E.26213
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X114.996 Y118.048 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 7.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X114.384 Y118.068 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 36/79
; update layer progress
M73 L36
M991 S0 P35 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z7.4 I.908 J-.81 P1  F42000
G1 X61.516 Y58.759 Z7.4
G1 Z7.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z7.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z7.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z7.6 F4000
            G39.3 S1
            G0 Z7.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z7.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z7.6 F42000
G1 X116.734 Y101.741 Z7.6
G1 Z7.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z7.6 F42000
G1 Z7.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.71 Y70.578 Z7.6 F42000
G1 X114.131 Y108.738 Z7.6
G1 Z7.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.331 Y108.738 E.10613
G1 X117.64 Y110.895 E.07229
G1 X117.838 Y112.274 E.0462
G1 X117.838 Y117.823 E.18409
G1 X117.652 Y118.387 E.01971
G1 X114.131 Y118.387 E.11677
G1 X114.131 Y108.798 E.31809
M204 S10000
G1 X113.724 Y108.331 F42000
G1 F8843.478
M204 S6000
G1 X117.684 Y108.331 E.13134
G1 X118.043 Y110.837 E.08399
G1 X118.245 Y112.245 E.04716
G1 X118.245 Y117.889 E.18723
G1 X117.946 Y118.794 E.03164
G1 X113.724 Y118.794 E.14004
G1 X113.724 Y108.391 E.3451
M204 S10000
G1 X113.435 Y107.924 F42000
G1 F8843.478
M204 S6000
G1 X118.036 Y107.924 E.15264
G1 X118.446 Y110.779 E.0957
G1 X118.652 Y112.215 E.04812
G1 X118.652 Y117.954 E.19036
G1 X118.24 Y119.201 E.04357
G1 X113.317 Y119.201 E.1633
G1 X113.317 Y108.118 E.36764
G1 X113.404 Y107.975 E.00555
M204 S10000
G1 X113.183 Y107.517 F42000
G1 F8843.478
M204 S6000
G1 X118.389 Y107.517 E.17269
G1 X118.849 Y110.722 E.1074
G1 X119.059 Y112.186 E.04909
G1 X119.059 Y118.02 E.1935
G1 X118.534 Y119.608 E.05551
G1 X112.91 Y119.608 E.18657
G1 X112.91 Y108.005 E.38491
G2 X113.158 Y107.571 I-2.935 J-1.962 E.01659
M204 S10000
G1 X112.918 Y107.11 F42000
G1 F8843.478
M204 S6000
G1 X118.742 Y107.11 E.1932
G1 X119.252 Y110.664 E.1191
G1 X119.466 Y112.157 E.05005
G1 X119.466 Y118.085 E.19663
G1 X118.829 Y120.016 E.06744
G1 X112.503 Y120.016 E.20984
G1 X112.503 Y107.876 E.4027
G2 X112.893 Y107.164 I-5 J-3.203 E.02693
M204 S250
M73 P78 R5
G1 X112.638 Y106.718 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X119.082 Y106.718 E.19799
G1 X119.64 Y110.608 E.12077
G1 X119.858 Y112.129 E.04722
G1 X119.858 Y118.148 E.18494
G1 X119.112 Y120.408 E.07312
G1 X112.111 Y120.408 E.21513
G1 X112.111 Y107.748 E.389
G2 X112.619 Y106.774 I-2.984 J-2.178 E.03386
; WIPE_START
M204 S6000
G1 X114.619 Y106.757 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X115.319 Y110.482 Z7.6 F42000
G1 Z7.2
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X115.319 Y110.142 E.01128
G1 X116.607 Y110.142 E.04273
G2 X117.223 Y110.436 I.672 J-.613 E.0232
G1 X117.49 Y112.452 E.06744
G3 X116.731 Y112.511 I-.443 J-.776 E.02609
G3 X115.682 Y111.676 I2.407 J-4.097 E.04461
G1 X115.319 Y111.542 E.01285
G1 X115.319 Y113.589 E.06791
G1 X115.682 Y113.612 E.01208
G1 X116.206 Y113.969 E.02104
G2 X117.255 Y114.641 I1.354 J-.958 E.04234
G1 X117.49 Y114.621 E.00782
G1 X117.49 Y116.645 E.06714
G3 X116.731 Y116.704 I-.443 J-.776 E.02609
G3 X115.682 Y115.869 I2.406 J-4.096 E.04461
G1 X115.319 Y115.735 E.01285
G1 X115.319 Y117.363 E.05401
M204 S10000
G1 X115.208 Y117.962 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.284 Y117.962 E.07518
M204 S10000
G1 X115.208 Y117.962 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X115.058 Y117.889 E.0059
; LINE_WIDTH: 0.433754
G1 F9211.083
G1 X114.922 Y117.681 E.00794
G1 X114.92 Y117.647 E.00108
G1 X114.92 Y110.031 E.24255
; LINE_WIDTH: 0.455204
G1 F8731.86
G1 X114.924 Y109.969 E.00207
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X114.927 Y109.908 E.00229
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X114.931 Y109.846 E.00251
; LINE_WIDTH: 0.573558
G1 F6784.295
G1 X115.047 Y109.715 E.00757
G1 X115.208 Y109.689 E.00707
; LINE_WIDTH: 0.541149
G1 F7225.597
G1 X117.01 Y109.689 E.07315
G1 X116.938 Y109.191 E.02044
G1 X115.208 Y109.191 E.07025
; LINE_WIDTH: 0.554223
G1 F7040.842
G1 X114.909 Y109.204 E.01247
; LINE_WIDTH: 0.579768
G1 F6705.807
G1 X114.61 Y109.217 E.01309
G1 X114.596 Y109.707 E.02147
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X114.574 Y109.815 E.00449
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X114.552 Y109.923 E.00409
; LINE_WIDTH: 0.433705
G1 F9212.228
G1 X114.53 Y110.031 E.0035
G1 X114.536 Y117.983 E.25323
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X115.148 Y117.963 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 7.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X114.536 Y117.983 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 37/79
; update layer progress
M73 L37
M991 S0 P36 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z7.6 I.907 J-.812 P1  F42000
G1 X61.516 Y58.759 Z7.6
G1 Z7.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z7.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z7.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z7.8 F4000
            G39.3 S1
            G0 Z7.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z7.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z7.8 F42000
G1 X116.734 Y101.741 Z7.8
G1 Z7.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z7.8 F42000
G1 Z7.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.738 Y70.58 Z7.8 F42000
G1 X114.283 Y108.933 Z7.8
G1 Z7.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.359 Y108.933 E.10202
G1 X117.698 Y111.302 E.07937
G1 X117.876 Y112.537 E.04141
G1 X117.876 Y117.709 E.17154
G1 X117.68 Y118.302 E.02075
G1 X114.283 Y118.302 E.11266
G1 X114.283 Y108.993 E.30881
M204 S10000
G1 X113.876 Y108.526 F42000
G1 F8843.478
M204 S6000
G1 X117.712 Y108.526 E.12722
G1 X118.101 Y111.244 E.09108
G1 X118.283 Y112.508 E.04237
G1 X118.283 Y117.774 E.17467
G1 X117.974 Y118.71 E.03268
G1 X113.876 Y118.71 E.13593
G1 X113.876 Y108.586 E.33581
M204 S10000
G1 X113.469 Y108.119 F42000
G1 F8843.478
M204 S6000
G1 X118.064 Y108.119 E.15243
G1 X118.504 Y111.186 E.10278
G1 X118.69 Y112.479 E.04333
G1 X118.69 Y117.84 E.17781
G1 X118.268 Y119.117 E.04461
G1 X113.469 Y119.117 E.15919
G1 X113.469 Y108.179 E.36282
M204 S10000
G1 X113.062 Y107.712 F42000
G1 F8843.478
M204 S6000
G1 X118.417 Y107.712 E.17764
G1 X118.907 Y111.128 E.11449
G1 X119.097 Y112.45 E.0443
G1 X119.097 Y117.905 E.18095
G1 X118.562 Y119.524 E.05655
G1 X113.062 Y119.524 E.18246
G1 X113.062 Y107.772 E.38983
M204 S10000
G1 X112.834 Y107.305 F42000
G1 F8843.478
M204 S6000
G1 X118.77 Y107.305 E.19691
G1 X119.31 Y111.071 E.12619
G1 X119.504 Y112.421 E.04526
G1 X119.504 Y117.97 E.18408
G1 X118.857 Y119.931 E.06848
G1 X112.655 Y119.931 E.20572
G1 X112.655 Y107.64 E.40771
G2 X112.809 Y107.36 I-1.936 J-1.249 E.01063
M204 S250
G1 X112.573 Y106.913 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X119.11 Y106.913 E.20085
G1 X119.698 Y111.015 E.12733
G1 X119.896 Y112.393 E.04278
G1 X119.896 Y118.034 E.17331
G1 X119.14 Y120.323 E.07408
G1 X112.263 Y120.323 E.21132
G1 X112.263 Y107.53 E.39309
G2 X112.55 Y106.968 I-4.507 J-2.653 E.0194
; WIPE_START
M204 S6000
G1 X114.55 Y106.951 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.454 Y112.05 Z7.8 F42000
G1 Z7.4
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.223 Y110.438 E.05401
G1 X116.692 Y110.337 E.01792
G1 X115.471 Y110.337 E.04051
G1 X115.471 Y111.534 E.03972
G1 X115.682 Y111.565 E.00709
G3 X116.731 Y112.39 I-6.064 J8.791 E.04426
G1 X117.255 Y112.539 E.01808
G1 X117.518 Y112.494 E.00885
M73 P79 R5
G1 X117.527 Y114.551 E.06824
G3 X116.731 Y114.558 I-.406 J-.828 E.02734
G3 X115.682 Y113.734 I6.064 J-8.791 E.04426
G1 X115.471 Y113.674 E.00729
G1 X115.471 Y115.727 E.06812
G1 X115.682 Y115.758 E.00709
G3 X116.731 Y116.583 I-6.067 J8.794 E.04426
G1 X117.255 Y116.732 E.01808
G1 X117.527 Y116.685 E.00918
G1 X117.527 Y117.451 E.0254
G1 X116.665 Y117.451 E.02861
M204 S10000
G1 X115.36 Y117.877 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.312 Y117.877 E.07069
M204 S10000
G1 X115.36 Y117.877 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X115.21 Y117.805 E.0059
; LINE_WIDTH: 0.433776
G1 F9210.569
G1 X115.074 Y117.596 E.00794
G1 X115.072 Y117.562 E.00108
G1 X115.072 Y110.226 E.23365
; LINE_WIDTH: 0.455204
G1 F8731.86
G1 X115.076 Y110.164 E.00207
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X115.079 Y110.103 E.00229
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X115.083 Y110.041 E.00251
; LINE_WIDTH: 0.573558
G1 F6784.295
G1 X115.199 Y109.91 E.00757
G1 X115.36 Y109.884 E.00707
; LINE_WIDTH: 0.541149
G1 F7225.598
G1 X117.038 Y109.884 E.06812
G1 X116.966 Y109.386 E.02044
G1 X115.36 Y109.386 E.06522
; LINE_WIDTH: 0.554223
G1 F7040.842
G1 X115.061 Y109.399 E.01247
; LINE_WIDTH: 0.579768
G1 F6705.807
G1 X114.762 Y109.412 E.01309
G1 X114.748 Y109.903 E.02147
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X114.726 Y110.01 E.00449
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X114.704 Y110.118 E.00409
; LINE_WIDTH: 0.433725
G1 F9211.765
G1 X114.682 Y110.226 E.0035
G1 X114.688 Y117.898 E.24432
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X115.3 Y117.879 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 7.6
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X114.688 Y117.898 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 38/79
; update layer progress
M73 L38
M991 S0 P37 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z7.8 I.905 J-.814 P1  F42000
G1 X61.516 Y58.759 Z7.8
G1 Z7.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z8 F4000
            G39.3 S1
            G0 Z8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z7.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z8 F42000
G1 X116.734 Y101.741 Z8
G1 Z7.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z8 F42000
G1 Z7.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.765 Y70.581 Z8 F42000
G1 X114.435 Y109.128 Z8
G1 Z7.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.387 Y109.128 E.0979
G1 X117.757 Y111.708 E.08646
G1 X117.914 Y112.801 E.03662
G1 X117.914 Y117.594 E.15899
G1 X117.708 Y118.218 E.02179
G1 X114.435 Y118.218 E.10855
G1 X114.435 Y109.188 E.29952
M204 S10000
G1 X114.028 Y108.721 F42000
G1 F8843.478
M204 S6000
G1 X117.74 Y108.721 E.12311
G1 X118.16 Y111.651 E.09816
G1 X118.321 Y112.772 E.03758
G1 X118.321 Y117.659 E.16212
G1 X118.002 Y118.625 E.03372
G1 X114.028 Y118.625 E.13181
G1 X114.028 Y108.781 E.32653
M204 S10000
G1 X113.621 Y108.314 F42000
G1 F8843.478
M204 S6000
G1 X118.092 Y108.314 E.14832
G1 X118.563 Y111.593 E.10987
G1 X118.728 Y112.743 E.03855
G1 X118.728 Y117.725 E.16526
G1 X118.296 Y119.032 E.04565
G1 X113.621 Y119.032 E.15508
G1 X113.621 Y108.374 E.35353
M204 S10000
G1 X113.214 Y107.907 F42000
G1 F8843.478
M204 S6000
G1 X118.445 Y107.907 E.17353
G1 X118.966 Y111.535 E.12157
G1 X119.135 Y112.714 E.03951
G1 X119.135 Y117.79 E.16839
G1 X118.59 Y119.439 E.05759
G1 X113.214 Y119.439 E.17834
G1 X113.214 Y107.967 E.38054
M204 S10000
G1 X112.807 Y107.5 F42000
G1 F8843.478
M204 S6000
G1 X118.798 Y107.5 E.19873
G1 X119.369 Y111.477 E.13328
G1 X119.542 Y112.685 E.04047
G1 X119.542 Y117.856 E.17153
G1 X118.885 Y119.846 E.06952
G1 X112.807 Y119.846 E.20161
G1 X112.807 Y107.56 E.40754
M204 S250
G1 X112.493 Y107.108 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X119.138 Y107.108 E.20417
G1 X119.757 Y111.422 E.1339
G1 X119.934 Y112.657 E.03835
G1 X119.934 Y117.919 E.16169
G1 X119.168 Y120.238 E.07504
G1 X112.415 Y120.238 E.20751
G1 X112.415 Y107.266 E.39861
G1 X112.467 Y107.162 E.00357
; WIPE_START
M204 S6000
G1 X114.467 Y107.146 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.358 Y110.532 Z8 F42000
G1 Z7.6
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X115.623 Y110.532 E.02437
G1 X115.623 Y111.425 E.02964
G1 X115.682 Y111.421 E.00198
G3 X116.731 Y112.293 I-.928 J2.181 E.04588
G1 X117.255 Y112.564 E.01958
G1 X117.53 Y112.58 E.00915
G1 X117.565 Y114.491 E.06341
G3 X116.731 Y114.703 I-.655 J-.831 E.02942
G3 X115.682 Y113.831 I.928 J-2.181 E.04588
G1 X115.623 Y113.8 E.00222
G1 X115.623 Y115.619 E.06033
G1 X115.682 Y115.614 E.00198
G3 X116.731 Y116.486 I-.928 J2.181 E.04588
G1 X117.255 Y116.757 E.01958
G1 X117.565 Y116.775 E.01032
G1 X117.565 Y117.366 E.01961
G1 X116.528 Y117.366 E.0344
M204 S10000
G1 X115.512 Y117.792 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.34 Y117.792 E.0662
M204 S10000
G1 X115.512 Y117.792 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X115.362 Y117.72 E.0059
; LINE_WIDTH: 0.433799
G1 F9210.016
G1 X115.226 Y117.511 E.00794
G1 X115.224 Y117.477 E.00108
M73 P79 R4
G1 X115.224 Y110.421 E.22474
; LINE_WIDTH: 0.455204
G1 F8731.86
G1 X115.228 Y110.36 E.00207
; LINE_WIDTH: 0.49929
G1 F7888.336
M73 P80 R4
G1 X115.231 Y110.298 E.00229
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X115.235 Y110.236 E.00251
; LINE_WIDTH: 0.573558
G1 F6784.295
G1 X115.351 Y110.105 E.00757
G1 X115.512 Y110.079 E.00707
; LINE_WIDTH: 0.541149
G1 F7225.599
G1 X117.066 Y110.079 E.06308
G1 X116.994 Y109.581 E.02044
G1 X115.512 Y109.581 E.06018
; LINE_WIDTH: 0.554223
G1 F7040.842
G1 X115.213 Y109.594 E.01247
; LINE_WIDTH: 0.579768
G1 F6705.807
G1 X114.914 Y109.607 E.01309
G1 X114.9 Y110.098 E.02147
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X114.878 Y110.206 E.00449
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X114.856 Y110.313 E.00409
; LINE_WIDTH: 0.433746
G1 F9211.268
G1 X114.834 Y110.421 E.0035
G1 X114.84 Y117.813 E.23542
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X115.452 Y117.794 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 7.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X114.84 Y117.813 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 39/79
; update layer progress
M73 L39
M991 S0 P38 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z8 I.903 J-.816 P1  F42000
G1 X61.516 Y58.759 Z8
G1 Z7.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z8.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z8.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z8.2 F4000
            G39.3 S1
            G0 Z8.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z7.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z8.2 F42000
G1 X116.734 Y101.741 Z8.2
G1 Z7.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z8.2 F42000
G1 Z7.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.791 Y70.583 Z8.2 F42000
G1 X114.587 Y109.324 Z8.2
G1 Z7.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.415 Y109.324 E.09379
G1 X117.815 Y112.115 E.09355
G1 X117.951 Y113.065 E.03183
G1 X117.951 Y117.479 E.14643
G1 X117.736 Y118.133 E.02283
G1 X114.587 Y118.133 E.10443
G1 X114.587 Y109.384 E.29023
M204 S10000
G1 X114.18 Y108.916 F42000
G1 F8843.478
M204 S6000
G1 X117.768 Y108.916 E.119
G1 X118.218 Y112.057 E.10525
G1 X118.358 Y113.036 E.0328
G1 X118.358 Y117.545 E.14957
G1 X118.03 Y118.54 E.03476
G1 X114.18 Y118.54 E.1277
G1 X114.18 Y108.976 E.31724
M204 S10000
G1 X113.773 Y108.509 F42000
G1 F8843.478
M204 S6000
G1 X118.12 Y108.509 E.14421
G1 X118.621 Y111.999 E.11696
G1 X118.766 Y113.007 E.03376
G1 X118.766 Y117.61 E.15271
G1 X118.324 Y118.947 E.0467
G1 X113.773 Y118.947 E.15096
G1 X113.773 Y108.569 E.34424
M204 S10000
G1 X113.366 Y108.102 F42000
G1 F8843.478
M204 S6000
G1 X118.473 Y108.102 E.16941
G1 X119.024 Y111.942 E.12866
G1 X119.173 Y112.978 E.03472
G1 X119.173 Y117.676 E.15584
G1 X118.618 Y119.354 E.05863
G1 X113.366 Y119.354 E.17423
G1 X113.366 Y108.162 E.37125
M204 S10000
G1 X112.959 Y107.695 F42000
G1 F8843.478
M204 S6000
G1 X118.826 Y107.695 E.19462
G1 X119.427 Y111.884 E.14036
G1 X119.58 Y112.949 E.03568
G1 X119.58 Y117.741 E.15898
G1 X118.913 Y119.761 E.07056
G1 X112.959 Y119.761 E.19749
G1 X112.959 Y107.755 E.39826
M204 S250
G1 X112.567 Y107.303 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X119.166 Y107.303 E.20277
G1 X119.815 Y111.828 E.14046
G1 X119.972 Y112.921 E.03391
G1 X119.972 Y117.804 E.15006
G1 X119.196 Y120.153 E.07601
G1 X112.567 Y120.153 E.2037
G1 X112.567 Y107.363 E.393
; WIPE_START
M204 S6000
G1 X114.567 Y107.345 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.918 Y110.727 Z8.2 F42000
G1 Z7.8
G1 E.8 F1800
; FEATURE: Sparse infill
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X115.775 Y110.727 E.0379
G1 X115.775 Y111.213 E.01611
G3 X116.206 Y111.36 I.112 J.377 E.01614
G1 X116.731 Y112.211 E.03315
G2 X117.551 Y112.723 I1.127 J-.892 E.03271
G3 X117.603 Y114.432 I-5.93 J1.038 E.05691
G3 X116.468 Y114.923 I-1.241 J-1.315 E.04185
G1 X116.206 Y114.763 E.01018
G1 X115.775 Y114.063 E.02729
G1 X115.775 Y115.406 E.04456
G3 X116.206 Y115.553 I.112 J.377 E.01614
G1 X116.731 Y116.404 E.03315
G2 X117.603 Y116.934 I1.178 J-.957 E.03454
G1 X117.603 Y117.281 E.01152
G1 X116.322 Y117.281 E.04249
M204 S10000
G1 X115.664 Y117.707 F42000
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.48739
G1 F8099.534
M204 S6000
G1 X117.368 Y117.707 E.06171
M204 S10000
G1 X115.664 Y117.707 F42000
; LINE_WIDTH: 0.4774
G1 F8285.767
M204 S6000
G1 X115.514 Y117.635 E.0059
; LINE_WIDTH: 0.433825
G1 F9209.419
G1 X115.378 Y117.426 E.00794
G1 X115.376 Y117.392 E.00108
G1 X115.376 Y110.616 E.21584
; LINE_WIDTH: 0.455204
G1 F8731.86
G1 X115.38 Y110.555 E.00207
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X115.383 Y110.493 E.00229
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X115.387 Y110.432 E.00251
; LINE_WIDTH: 0.573558
G1 F6784.295
G1 X115.503 Y110.301 E.00757
G1 X115.664 Y110.274 E.00707
; LINE_WIDTH: 0.541149
G1 F7225.601
G1 X117.094 Y110.274 E.05805
G1 X117.022 Y109.776 E.02044
G1 X115.664 Y109.776 E.05515
; LINE_WIDTH: 0.554223
G1 F7040.842
G1 X115.365 Y109.789 E.01247
; LINE_WIDTH: 0.579768
G1 F6705.807
G1 X115.066 Y109.802 E.01309
G1 X115.052 Y110.293 E.02147
; LINE_WIDTH: 0.543377
G1 F7193.43
G1 X115.03 Y110.401 E.00449
; LINE_WIDTH: 0.49929
G1 F7888.336
G1 X115.008 Y110.509 E.00409
; LINE_WIDTH: 0.433769
G1 F9210.733
G1 X114.986 Y110.616 E.0035
G1 X114.992 Y117.728 E.22651
; LINE_WIDTH: 0.466135
G1 F8506.314
G1 X115.604 Y117.709 E.02112
; CHANGE_LAYER
; Z_HEIGHT: 8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8506.314
G1 X114.992 Y117.728 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 40/79
; update layer progress
M73 L40
M991 S0 P39 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z8.2 I.901 J-.818 P1  F42000
G1 X61.516 Y58.759 Z8.2
G1 Z8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X61.516 Y93.741 E1.16041
G1 X60.534 Y93.741 E.03257
G1 X60.534 Y58.759 E1.16041
G1 X61.456 Y58.759 E.03058
M204 S10000
G1 X61.923 Y58.352 F42000
G1 F8843.478
M204 S6000
G1 X61.923 Y94.148 E1.18741
G1 X60.127 Y94.148 E.05957
G1 X60.127 Y58.352 E1.18741
G1 X61.863 Y58.352 E.05758
M204 S250
G1 X62.315 Y57.96 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z8.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z8.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z8.4 F4000
            G39.3 S1
            G0 Z8.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.025 Y58.963 F42000
G1 Z8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X61.025 Y93.537 E1.61905
; WIPE_START
G1 X61.025 Y91.537 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X68.533 Y92.912 Z8.4 F42000
G1 X116.734 Y101.741 Z8.4
G1 Z8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X116.734 Y60.759 E1.35944
G1 X117.716 Y60.759 E.03257
G1 X117.716 Y101.741 E1.35944
G1 X116.794 Y101.741 E.03058
M204 S10000
G1 X116.327 Y102.148 F42000
M73 P81 R4
G1 F8843.478
M204 S6000
G1 X116.327 Y60.352 E1.38645
G1 X118.123 Y60.352 E.05957
G1 X118.123 Y102.148 E1.38645
G1 X116.387 Y102.148 E.05758
M204 S250
G1 X115.935 Y102.54 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.225 Y101.537 Z8.4 F42000
G1 Z8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.61758
G1 F6264.574
M204 S6000
G1 X117.225 Y60.963 E1.90001
; WIPE_START
G1 X117.225 Y62.963 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.818 Y70.584 Z8.4 F42000
G1 X114.739 Y109.519 Z8.4
G1 Z8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.443 Y109.519 E.08968
G1 X117.873 Y112.522 E.10063
G1 X117.989 Y113.329 E.02704
G1 X117.989 Y117.365 E.13388
G1 X117.764 Y118.048 E.02387
G1 X114.739 Y118.048 E.10032
G1 X114.739 Y109.579 E.28094
M204 S10000
G1 X114.332 Y109.112 F42000
G1 F8843.478
M204 S6000
G1 X117.796 Y109.112 E.11488
G1 X118.276 Y112.464 E.11234
G1 X118.396 Y113.3 E.02801
G1 X118.396 Y117.43 E.13702
G1 X118.058 Y118.455 E.0358
G1 X114.332 Y118.455 E.12359
G1 X114.332 Y109.172 E.30795
M204 S10000
G1 X113.925 Y108.705 F42000
G1 F8843.478
M204 S6000
G1 X118.148 Y108.705 E.14009
G1 X118.679 Y112.406 E.12404
G1 X118.803 Y113.271 E.02897
G1 X118.803 Y117.496 E.14016
G1 X118.352 Y118.862 E.04774
G1 X113.925 Y118.862 E.14685
G1 X113.925 Y108.765 E.33496
M204 S10000
G1 X113.518 Y108.298 F42000
G1 F8843.478
M204 S6000
G1 X118.501 Y108.298 E.1653
G1 X119.082 Y112.348 E.13575
G1 X119.21 Y113.242 E.02993
G1 X119.21 Y117.561 E.14329
G1 X118.646 Y119.269 E.05967
G1 X113.518 Y119.269 E.17012
G1 X113.518 Y108.358 E.36196
M204 S10000
G1 X113.111 Y107.89 F42000
G1 F8843.478
M204 S6000
G1 X118.854 Y107.89 E.19051
G1 X119.485 Y112.291 E.14745
G1 X119.618 Y113.212 E.0309
G1 X119.618 Y117.627 E.14643
G1 X118.941 Y119.676 E.0716
G1 X113.111 Y119.676 E.19338
G1 X113.111 Y107.95 E.38897
M204 S250
G1 X112.719 Y107.498 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X119.194 Y107.498 E.19896
G1 X119.873 Y112.235 E.14703
G1 X120.01 Y113.184 E.02948
G1 X120.01 Y117.69 E.13843
G1 X119.224 Y120.068 E.07697
G1 X112.719 Y120.068 E.19989
G1 X112.719 Y107.558 E.3844
; WIPE_START
M204 S6000
G1 X114.719 Y107.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.597 Y113.445 Z8.4 F42000
G1 Z8
G1 E.8 F1800
; FEATURE: Floating vertical shell
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X117.103 Y109.911 E.10964
G1 X115.131 Y109.911 E.06058
G1 X115.131 Y117.656 E.23798
G1 X117.48 Y117.656 E.07217
G1 X117.597 Y117.234 E.01346
G1 X117.597 Y113.505 E.11459
M204 S10000
G1 X116.776 Y110.288 F42000
G1 F9547.299
M204 S6000
G1 X115.508 Y110.288 E.03895
G1 X115.508 Y117.279 E.21481
G1 X117.208 Y117.279 E.05221
G2 X117.211 Y113.323 I-184.514 J-2.156 E.12155
G1 X116.785 Y110.347 E.09237
M204 S10000
G1 X116.61 Y111.788 F42000
; LINE_WIDTH: 0.444522
G1 F8964.106
M204 S6000
G1 X116.567 Y111.66 E.00443
; LINE_WIDTH: 0.493585
G1 F7988.195
G1 X116.524 Y111.531 E.00497
; LINE_WIDTH: 0.545898
G1 F7157.371
G1 X116.481 Y111.403 E.00554
G1 X116.4 Y110.722 E.02813
G1 X115.942 Y110.722 E.01876
G1 X115.959 Y111.441 E.02947
; LINE_WIDTH: 0.542649
G1 F7203.914
G1 X115.935 Y111.574 E.00551
; LINE_WIDTH: 0.493585
G1 F7988.195
G1 X115.91 Y111.707 E.00497
; LINE_WIDTH: 0.420286
G1 F9539.822
G1 X115.886 Y111.84 E.00416
G1 X115.886 Y116.902 E.15567
G1 X116.843 Y116.902 E.02944
G1 X116.843 Y113.445 E.10631
G1 X116.619 Y111.847 E.0496
M204 S10000
G1 X116.25 Y111.84 F42000
; Slow Down Start
; LINE_WIDTH: 0.39424
G1 F3000;_EXTRUDE_SET_SPEED
M204 S6000
G1 X116.364 Y113.445 E.04607
; Slow Down End
; Slow Down Start
; LINE_WIDTH: 0.62334
;_EXTRUDE_SET_SPEED
G1 X116.364 Y116.363 E.13804
; Slow Down End
; CHANGE_LAYER
; Z_HEIGHT: 8.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F3000
G1 X116.364 Y114.363 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 41/79
; update layer progress
M73 L41
M991 S0 P40 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z8.4 I.879 J-.842 P1  F42000
G1 X62.315 Y57.96 Z8.4
G1 Z8.2
G1 E.8 F1800
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X62.315 Y94.54 E1.124
G1 X59.735 Y94.54 E.07928
G1 X59.735 Y57.96 E1.124
G1 X62.255 Y57.96 E.07743
; WIPE_START
M204 S6000
G1 X62.258 Y59.96 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z8.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z8.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z8.6 F4000
            G39.3 S1
            G0 Z8.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X61.634 Y58.167 F42000
G1 Z8.2
G1 E.8 F1800
; FEATURE: Top surface
G1 F9547.055
M204 S2000
G1 X62.108 Y58.642 E.0206
G1 X62.108 Y59.175
G1 X61.1 Y58.167 E.04377
G1 X60.567 Y58.167
G1 X62.108 Y59.708 E.06695
G1 X62.108 Y60.241
G1 X60.034 Y58.167 E.09012
G1 X59.942 Y58.609
G1 X62.108 Y60.775 E.09409
G1 X62.108 Y61.308
G1 X59.942 Y59.143 E.09409
G1 X59.942 Y59.676
G1 X62.108 Y61.841 E.09409
G1 X62.108 Y62.374
G1 X59.942 Y60.209 E.09409
G1 X59.942 Y60.742
G1 X62.108 Y62.908 E.09409
G1 X62.108 Y63.441
G1 X59.942 Y61.276 E.09409
G1 X59.942 Y61.809
G1 X62.108 Y63.974 E.09409
G1 X62.108 Y64.507
G1 X59.942 Y62.342 E.09409
G1 X59.942 Y62.875
G1 X62.108 Y65.041 E.09409
G1 X62.108 Y65.574
G1 X59.942 Y63.409 E.09409
G1 X59.942 Y63.942
G1 X62.108 Y66.107 E.09409
G1 X62.108 Y66.64
G1 X59.942 Y64.475 E.09409
G1 X59.942 Y65.008
G1 X62.108 Y67.174 E.09409
G1 X62.108 Y67.707
G1 X59.942 Y65.542 E.09409
G1 X59.942 Y66.075
G1 X62.108 Y68.24 E.09409
G1 X62.108 Y68.773
G1 X59.942 Y66.608 E.09409
G1 X59.942 Y67.141
G1 X62.108 Y69.307 E.09409
G1 X62.108 Y69.84
G1 X59.942 Y67.675 E.09409
G1 X59.942 Y68.208
G1 X62.108 Y70.373 E.09409
G1 X62.108 Y70.906
G1 X59.942 Y68.741 E.09409
G1 X59.942 Y69.274
G1 X62.108 Y71.44 E.09409
G1 X62.108 Y71.973
G1 X59.942 Y69.808 E.09409
G1 X59.942 Y70.341
G1 X62.108 Y72.506 E.09409
G1 X62.108 Y73.039
G1 X59.942 Y70.874 E.09409
G1 X59.942 Y71.407
G1 X62.108 Y73.573 E.09409
G1 X62.108 Y74.106
G1 X59.942 Y71.941 E.09409
G1 X59.942 Y72.474
G1 X62.108 Y74.639 E.09409
G1 X62.108 Y75.172
G1 X59.942 Y73.007 E.09409
G1 X59.942 Y73.541
G1 X62.108 Y75.706 E.09409
G1 X62.108 Y76.239
G1 X59.942 Y74.074 E.09409
G1 X59.942 Y74.607
G1 X62.108 Y76.772 E.09409
G1 X62.108 Y77.306
G1 X59.942 Y75.14 E.09409
G1 X59.942 Y75.674
G1 X62.108 Y77.839 E.09409
G1 X62.108 Y78.372
G1 X59.942 Y76.207 E.09409
G1 X59.942 Y76.74
G1 X62.108 Y78.905 E.09409
G1 X62.108 Y79.439
G1 X59.942 Y77.273 E.09409
G1 X59.942 Y77.807
G1 X62.108 Y79.972 E.09409
G1 X62.108 Y80.505
G1 X59.942 Y78.34 E.09409
G1 X59.942 Y78.873
G1 X62.108 Y81.038 E.09409
G1 X62.108 Y81.572
G1 X59.942 Y79.406 E.09409
G1 X59.942 Y79.94
G1 X62.108 Y82.105 E.09409
G1 X62.108 Y82.638
G1 X59.942 Y80.473 E.09409
G1 X59.942 Y81.006
G1 X62.108 Y83.171 E.09409
G1 X62.108 Y83.705
G1 X59.942 Y81.539 E.09409
G1 X59.942 Y82.073
G1 X62.108 Y84.238 E.09409
G1 X62.108 Y84.771
G1 X59.942 Y82.606 E.09409
G1 X59.942 Y83.139
G1 X62.108 Y85.304 E.09409
G1 X62.108 Y85.838
G1 X59.942 Y83.672 E.09409
M73 P82 R4
G1 X59.942 Y84.206
G1 X62.108 Y86.371 E.09409
G1 X62.108 Y86.904
G1 X59.942 Y84.739 E.09409
G1 X59.942 Y85.272
G1 X62.108 Y87.437 E.09409
G1 X62.108 Y87.971
G1 X59.942 Y85.805 E.09409
G1 X59.942 Y86.339
G1 X62.108 Y88.504 E.09409
G1 X62.108 Y89.037
G1 X59.942 Y86.872 E.09409
G1 X59.942 Y87.405
G1 X62.108 Y89.57 E.09409
G1 X62.108 Y90.104
G1 X59.942 Y87.938 E.09409
G1 X59.942 Y88.472
G1 X62.108 Y90.637 E.09409
G1 X62.108 Y91.17
G1 X59.942 Y89.005 E.09409
G1 X59.942 Y89.538
G1 X62.108 Y91.703 E.09409
G1 X62.108 Y92.237
G1 X59.942 Y90.072 E.09409
G1 X59.942 Y90.605
G1 X62.108 Y92.77 E.09409
G1 X62.108 Y93.303
G1 X59.942 Y91.138 E.09409
G1 X59.942 Y91.671
G1 X62.108 Y93.836 E.09409
G1 X62.07 Y94.333
G1 X59.942 Y92.205 E.09248
G1 X59.942 Y92.738
G1 X61.537 Y94.333 E.0693
G1 X61.004 Y94.333
G1 X59.942 Y93.271 E.04613
G1 X59.942 Y93.804
G1 X60.471 Y94.333 E.02296
; WIPE_START
M204 S6000
G1 X59.942 Y93.804 E-.28393
G1 X59.942 Y93.271 E-.20264
G1 X60.451 Y93.78 E-.27343
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X67.99 Y94.97 Z8.6 F42000
G1 X115.935 Y102.54 Z8.6
G1 Z8.2
G1 E.8 F1800
; FEATURE: Outer wall
G1 F3600
M204 S5000
G1 X115.935 Y59.96 E1.30837
G1 X118.515 Y59.96 E.07928
G1 X118.515 Y102.54 E1.30837
G1 X115.995 Y102.54 E.07743
; WIPE_START
M204 S6000
G1 X115.992 Y100.54 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.438 Y92.921 Z8.6 F42000
G1 X118.308 Y60.983 Z8.6
G1 Z8.2
G1 E.8 F1800
; FEATURE: Top surface
G1 F9547.055
M204 S2000
G1 X117.493 Y60.167 E.03542
G1 X116.959 Y60.167
G1 X118.308 Y61.516 E.05859
G1 X118.308 Y62.049
G1 X116.426 Y60.167 E.08177
G1 X116.142 Y60.417
G1 X118.308 Y62.582 E.09409
G1 X118.308 Y63.116
G1 X116.142 Y60.95 E.09409
G1 X116.142 Y61.484
G1 X118.308 Y63.649 E.09409
G1 X118.308 Y64.182
G1 X116.142 Y62.017 E.09409
G1 X116.142 Y62.55
G1 X118.308 Y64.715 E.09409
G1 X118.308 Y65.249
G1 X116.142 Y63.083 E.09409
G1 X116.142 Y63.617
G1 X118.308 Y65.782 E.09409
G1 X118.308 Y66.315
G1 X116.142 Y64.15 E.09409
G1 X116.142 Y64.683
G1 X118.308 Y66.848 E.09409
G1 X118.308 Y67.382
G1 X116.142 Y65.216 E.09409
G1 X116.142 Y65.75
G1 X118.308 Y67.915 E.09409
G1 X118.308 Y68.448
G1 X116.142 Y66.283 E.09409
G1 X116.142 Y66.816
G1 X118.308 Y68.981 E.09409
G1 X118.308 Y69.515
G1 X116.142 Y67.349 E.09409
G1 X116.142 Y67.883
G1 X118.308 Y70.048 E.09409
G1 X118.308 Y70.581
G1 X116.142 Y68.416 E.09409
G1 X116.142 Y68.949
G1 X118.308 Y71.114 E.09409
G1 X118.308 Y71.648
G1 X116.142 Y69.482 E.09409
G1 X116.142 Y70.016
G1 X118.308 Y72.181 E.09409
G1 X118.308 Y72.714
G1 X116.142 Y70.549 E.09409
G1 X116.142 Y71.082
G1 X118.308 Y73.247 E.09409
G1 X118.308 Y73.781
G1 X116.142 Y71.615 E.09409
G1 X116.142 Y72.149
G1 X118.308 Y74.314 E.09409
G1 X118.308 Y74.847
G1 X116.142 Y72.682 E.09409
G1 X116.142 Y73.215
G1 X118.308 Y75.38 E.09409
G1 X118.308 Y75.914
G1 X116.142 Y73.748 E.09409
G1 X116.142 Y74.282
G1 X118.308 Y76.447 E.09409
G1 X118.308 Y76.98
G1 X116.142 Y74.815 E.09409
G1 X116.142 Y75.348
G1 X118.308 Y77.513 E.09409
G1 X118.308 Y78.047
G1 X116.142 Y75.882 E.09409
G1 X116.142 Y76.415
G1 X118.308 Y78.58 E.09409
G1 X118.308 Y79.113
G1 X116.142 Y76.948 E.09409
G1 X116.142 Y77.481
G1 X118.308 Y79.647 E.09409
G1 X118.308 Y80.18
G1 X116.142 Y78.015 E.09409
G1 X116.142 Y78.548
G1 X118.308 Y80.713 E.09409
G1 X118.308 Y81.246
G1 X116.142 Y79.081 E.09409
G1 X116.142 Y79.614
G1 X118.308 Y81.78 E.09409
G1 X118.308 Y82.313
G1 X116.142 Y80.148 E.09409
G1 X116.142 Y80.681
G1 X118.308 Y82.846 E.09409
G1 X118.308 Y83.379
G1 X116.142 Y81.214 E.09409
G1 X116.142 Y81.747
G1 X118.308 Y83.913 E.09409
G1 X118.308 Y84.446
G1 X116.142 Y82.281 E.09409
G1 X116.142 Y82.814
G1 X118.308 Y84.979 E.09409
G1 X118.308 Y85.512
G1 X116.142 Y83.347 E.09409
G1 X116.142 Y83.88
G1 X118.308 Y86.046 E.09409
G1 X118.308 Y86.579
G1 X116.142 Y84.414 E.09409
G1 X116.142 Y84.947
G1 X118.308 Y87.112 E.09409
G1 X118.308 Y87.645
G1 X116.142 Y85.48 E.09409
G1 X116.142 Y86.013
G1 X118.308 Y88.179 E.09409
G1 X118.308 Y88.712
G1 X116.142 Y86.547 E.09409
G1 X116.142 Y87.08
G1 X118.308 Y89.245 E.09409
G1 X118.308 Y89.778
G1 X116.142 Y87.613 E.09409
G1 X116.142 Y88.146
G1 X118.308 Y90.312 E.09409
G1 X118.308 Y90.845
G1 X116.142 Y88.68 E.09409
G1 X116.142 Y89.213
G1 X118.308 Y91.378 E.09409
G1 X118.308 Y91.911
G1 X116.142 Y89.746 E.09409
G1 X116.142 Y90.279
G1 X118.308 Y92.445 E.09409
G1 X118.308 Y92.978
G1 X116.142 Y90.813 E.09409
G1 X116.142 Y91.346
G1 X118.308 Y93.511 E.09409
G1 X118.308 Y94.044
G1 X116.142 Y91.879 E.09409
G1 X116.142 Y92.413
G1 X118.308 Y94.578 E.09409
G1 X118.308 Y95.111
G1 X116.142 Y92.946 E.09409
G1 X116.142 Y93.479
G1 X118.308 Y95.644 E.09409
G1 X118.308 Y96.177
G1 X116.142 Y94.012 E.09409
G1 X116.142 Y94.546
G1 X118.308 Y96.711 E.09409
G1 X118.308 Y97.244
G1 X116.142 Y95.079 E.09409
G1 X116.142 Y95.612
G1 X118.308 Y97.777 E.09409
G1 X118.308 Y98.311
G1 X116.142 Y96.145 E.09409
G1 X116.142 Y96.679
G1 X118.308 Y98.844 E.09409
G1 X118.308 Y99.377
G1 X116.142 Y97.212 E.09409
G1 X116.142 Y97.745
G1 X118.308 Y99.91 E.09409
G1 X118.308 Y100.444
G1 X116.142 Y98.278 E.09409
G1 X116.142 Y98.812
G1 X118.308 Y100.977 E.09409
G1 X118.308 Y101.51
G1 X116.142 Y99.345 E.09409
G1 X116.142 Y99.878
G1 X118.308 Y102.043 E.09409
G1 X118.064 Y102.333
G1 X116.142 Y100.411 E.08349
G1 X116.142 Y100.945
G1 X117.53 Y102.333 E.06032
G1 X116.997 Y102.333
G1 X116.142 Y101.478 E.03714
; WIPE_START
M204 S6000
G1 X116.997 Y102.333 E-.45934
G1 X117.53 Y102.333 E-.20264
G1 X117.348 Y102.15 E-.09802
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X114.99 Y109.409 Z8.6 F42000
G1 X114.891 Y109.714 Z8.6
G1 Z8.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F8843.478
M204 S6000
G1 X117.471 Y109.714 E.08556
G1 X117.932 Y112.928 E.10772
G1 X118.027 Y113.593 E.02226
G1 X118.027 Y117.25 E.12133
G1 X117.792 Y117.963 E.02491
G1 X114.891 Y117.963 E.09621
G1 X114.891 Y109.774 E.27165
M204 S10000
G1 X114.484 Y109.307 F42000
G1 F8843.478
M204 S6000
G1 X117.824 Y109.307 E.11077
G1 X118.335 Y112.871 E.11942
G1 X118.434 Y113.563 E.02322
G1 X118.434 Y117.316 E.12447
G1 X118.086 Y118.37 E.03684
G1 X114.484 Y118.37 E.11947
G1 X114.484 Y109.367 E.29866
M204 S10000
G1 X114.077 Y108.9 F42000
G1 F8843.478
M204 S6000
G1 X118.176 Y108.9 E.13598
G1 X118.738 Y112.813 E.13113
G1 X118.841 Y113.534 E.02418
G1 X118.841 Y117.381 E.1276
G1 X118.38 Y118.777 E.04878
G1 X114.077 Y118.777 E.14274
G1 X114.077 Y108.96 E.32567
M204 S10000
G1 X113.67 Y108.493 F42000
G1 F8843.478
M204 S6000
G1 X118.529 Y108.493 E.16119
G1 X119.141 Y112.755 E.14283
G1 X119.248 Y113.505 E.02514
G1 X119.248 Y117.447 E.13074
G1 X118.674 Y119.184 E.06071
G1 X113.67 Y119.184 E.166
G1 X113.67 Y108.553 E.35267
M204 S10000
G1 X113.263 Y108.086 F42000
G1 F8843.478
M204 S6000
G1 X118.882 Y108.086 E.18639
G1 X119.544 Y112.697 E.15454
G1 X119.655 Y113.476 E.02611
G1 X119.655 Y117.512 E.13388
G1 X118.969 Y119.592 E.07264
G1 X113.263 Y119.592 E.18927
G1 X113.263 Y108.146 E.37968
M204 S250
G1 X112.871 Y107.694 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F3600
M204 S5000
G1 X119.222 Y107.694 E.19515
G1 X119.932 Y112.642 E.15359
G1 X120.047 Y113.448 E.02504
G1 X120.047 Y117.575 E.12681
G1 X119.252 Y119.984 E.07794
G1 X112.871 Y119.984 E.19608
G1 X112.871 Y107.754 E.37579
; WIPE_START
M204 S6000
G1 X114.871 Y107.735 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X116.402 Y112.899 Z8.6 F42000
G1 Z8.2
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.413397
G1 F9717.21
M204 S6000
G1 X116.421 Y113.168 E.00812
; LINE_WIDTH: 0.45171
M73 P83 R4
G1 F8806.478
G1 X116.44 Y113.436 E.00896
; LINE_WIDTH: 0.507403
G1 F7750.561
G1 X116.459 Y113.704 E.01019
G1 X116.459 Y116.335 E.09958
M204 S10000
G1 X116.061 Y110.884 F42000
; LINE_WIDTH: 0.46696
G1 F8489.765
M204 S6000
G1 X116.061 Y111.096 E.00733
; LINE_WIDTH: 0.483664
G1 F8168.02
G1 X116.078 Y111.564 E.01682
; LINE_WIDTH: 0.51707
G1 F7592.534
G1 X116.094 Y112.032 E.0181
; LINE_WIDTH: 0.550477
G1 F7092.804
G1 X116.111 Y112.5 E.01938
; LINE_WIDTH: 0.542649
G1 F7203.914
G1 X116.087 Y112.633 E.00551
; LINE_WIDTH: 0.493585
G1 F7988.195
G1 X116.062 Y112.766 E.00497
; LINE_WIDTH: 0.420364
G1 F9537.843
G1 X116.038 Y112.899 E.00416
G1 X116.038 Y116.817 E.1205
G1 X116.881 Y116.817 E.02594
G1 X116.881 Y113.704 E.09574
G1 X116.762 Y112.847 E.02661
; LINE_WIDTH: 0.444522
G1 F8964.106
G1 X116.719 Y112.719 E.00443
; LINE_WIDTH: 0.493585
G1 F7988.195
G1 X116.676 Y112.591 E.00497
; LINE_WIDTH: 0.542649
G1 F7203.914
G1 X116.633 Y112.463 E.00551
; LINE_WIDTH: 0.550477
G1 F7092.804
G1 X116.583 Y111.997 E.01938
; LINE_WIDTH: 0.51707
G1 F7592.534
G1 X116.533 Y111.531 E.0181
; LINE_WIDTH: 0.47488
G1 F8334.117
G2 X116.457 Y110.884 I-9.11 J.741 E.02296
G1 X116.121 Y110.884 E.01182
M204 S10000
G1 X115.66 Y110.483 F42000
; LINE_WIDTH: 0.41999
G1 F9547.299
M204 S6000
G1 X115.66 Y117.194 E.20621
G1 X117.236 Y117.194 E.0484
G1 X117.258 Y116.395 E.02455
G1 X117.258 Y113.704 E.08269
G2 X116.804 Y110.483 I-183.318 J24.189 E.09996
G1 X115.72 Y110.483 E.03329
M204 S10000
G1 X115.283 Y110.106 F42000
G1 F9547.299
M204 S6000
G1 X115.283 Y117.571 E.22938
G1 X117.508 Y117.571 E.06836
G1 X117.635 Y117.114 E.01459
G1 X117.635 Y113.704 E.10475
G2 X117.131 Y110.106 I-147.25 J18.795 E.11165
G1 X115.343 Y110.106 E.05492
; CHANGE_LAYER
; Z_HEIGHT: 8.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X117.131 Y110.106 E-.67924
G1 X117.16 Y110.316 E-.08076
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 42/79
; update layer progress
M73 L42
M991 S0 P41 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z8.6 I.23 J-1.195 P1  F42000
G1 X115.043 Y109.909 Z8.6
G1 Z8.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1933
M204 S6000
G1 X117.499 Y109.909 E.08145
G1 X117.99 Y113.335 E.11481
G1 X118.065 Y113.856 E.01747
G1 X118.065 Y117.136 E.10878
G1 X117.82 Y117.878 E.02595
G1 X115.043 Y117.878 E.09209
G1 X115.043 Y109.969 E.26237
M204 S10000
G1 X114.636 Y109.502 F42000
G1 F1933
M204 S6000
G1 X117.852 Y109.502 E.10666
G1 X118.393 Y113.277 E.12651
G1 X118.472 Y113.827 E.01843
G1 X118.472 Y117.201 E.11192
G1 X118.114 Y118.286 E.03788
G1 X114.636 Y118.286 E.11536
G1 X114.636 Y109.562 E.28937
M204 S10000
G1 X114.229 Y109.095 F42000
G1 F1933
M204 S6000
G1 X118.204 Y109.095 E.13187
G1 X118.796 Y113.219 E.13821
G1 X118.879 Y113.798 E.01939
G1 X118.879 Y117.267 E.11505
G1 X118.408 Y118.693 E.04982
G1 X114.229 Y118.693 E.13863
G1 X114.229 Y109.155 E.31638
M204 S10000
G1 X113.822 Y108.688 F42000
G1 F1933
M204 S6000
G1 X118.557 Y108.688 E.15707
G1 X119.199 Y113.162 E.14992
G1 X119.286 Y113.769 E.02036
G1 X119.286 Y117.332 E.11819
G1 X118.702 Y119.1 E.06175
G1 X113.822 Y119.1 E.16189
G1 X113.822 Y108.748 E.34339
M204 S10000
G1 X113.415 Y108.281 F42000
G1 F1933
M204 S6000
G1 X118.91 Y108.281 E.18228
G1 X119.602 Y113.104 E.16162
G1 X119.693 Y113.74 E.02132
G1 X119.693 Y117.397 E.12132
G1 X118.997 Y119.507 E.07368
G1 X113.415 Y119.507 E.18516
G1 X113.415 Y108.341 E.37039
M204 S250
G1 X113.023 Y107.889 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1933
M204 S5000
G1 X119.25 Y107.889 E.19134
G1 X119.99 Y113.048 E.16016
G1 X120.085 Y113.712 E.02061
G1 X120.085 Y117.461 E.11518
G1 X119.28 Y119.899 E.0789
G1 X113.023 Y119.899 E.19227
G1 X113.023 Y107.949 E.36719
; WIPE_START
G1 F3600
M204 S6000
G1 X115.023 Y107.93 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z8.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z8.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z8.8 F4000
            G39.3 S1
            G0 Z8.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X116.554 Y116.368 F42000
G1 Z8.4
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.39502
G1 F1933
M204 S6000
G1 X116.554 Y114.024 E.06724
M204 S10000
G1 X116.18 Y111.046 F42000
; LINE_WIDTH: 0.40054
G1 F1933
M204 S6000
G1 X116.18 Y111.224 E.00521
; LINE_WIDTH: 0.42137
G1 X116.201 Y111.808 E.01802
; LINE_WIDTH: 0.46303
G1 X116.221 Y112.392 E.02
; LINE_WIDTH: 0.50469
G1 X116.242 Y112.976 E.02198
; LINE_WIDTH: 0.54635
G1 X116.263 Y113.56 E.02397
; LINE_WIDTH: 0.542649
G1 X116.239 Y113.695 E.00558
; LINE_WIDTH: 0.493585
G1 X116.214 Y113.829 E.00503
; LINE_WIDTH: 0.420515
G1 X116.19 Y113.964 E.00422
G1 X116.19 Y116.732 E.08518
G1 X116.919 Y116.732 E.02244
G1 X116.919 Y113.964 E.08518
; LINE_WIDTH: 0.444522
G1 X116.874 Y113.817 E.00503
; LINE_WIDTH: 0.493585
G1 X116.829 Y113.67 E.00565
; LINE_WIDTH: 0.542649
G1 X116.785 Y113.523 E.00626
; LINE_WIDTH: 0.54635
G1 X116.722 Y112.942 E.02397
; LINE_WIDTH: 0.50469
G1 X116.66 Y112.361 E.02198
; LINE_WIDTH: 0.46303
G1 X116.598 Y111.78 E.02
; LINE_WIDTH: 0.412553
G2 X116.514 Y111.046 I-10.344 J.815 E.02227
G1 X116.24 Y111.046 E.00825
M204 S10000
G1 X115.812 Y110.678 F42000
; LINE_WIDTH: 0.41999
G1 F1933
M204 S6000
G1 X115.812 Y117.109 E.1976
G1 X117.264 Y117.109 E.04459
G1 X117.296 Y116.993 E.0037
G1 X117.296 Y113.964 E.09308
G2 X116.832 Y110.678 I-112.033 J14.137 E.10196
G1 X115.872 Y110.678 E.02948
M204 S10000
G1 X115.435 Y110.301 F42000
G1 F1933
M204 S6000
G1 X115.435 Y117.486 E.22077
G1 X117.536 Y117.486 E.06455
G1 X117.673 Y116.993 E.01572
G1 X117.673 Y113.964 E.09308
G1 X117.159 Y110.301 E.11365
G1 X115.495 Y110.301 E.05111
; CHANGE_LAYER
; Z_HEIGHT: 8.6
; LAYER_HEIGHT: 0.200001
; WIPE_START
G1 F9547.299
G1 X117.159 Y110.301 E-.63212
G1 X117.206 Y110.634 E-.12788
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 43/79
; update layer progress
M73 L43
M991 S0 P42 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z8.8 I.31 J-1.177 P1  F42000
G1 X115.195 Y110.104 Z8.8
G1 Z8.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1842
M204 S6000
G1 X117.527 Y110.104 E.07734
G1 X118.048 Y113.742 E.12189
G1 X118.103 Y114.12 E.01268
G1 X118.103 Y117.021 E.09623
G1 X117.848 Y117.794 E.02699
G1 X115.195 Y117.794 E.08798
G1 X115.195 Y110.164 E.25308
M204 S10000
G1 X114.788 Y109.697 F42000
G1 F1842
M204 S6000
G1 X117.88 Y109.697 E.10254
G1 X118.451 Y113.684 E.1336
G1 X118.51 Y114.091 E.01364
G1 X118.51 Y117.086 E.09936
G1 X118.142 Y118.201 E.03893
G1 X114.788 Y118.201 E.11125
G1 X114.788 Y109.757 E.28008
M204 S10000
G1 X114.381 Y109.29 F42000
G1 F1842
M204 S6000
G1 X118.232 Y109.29 E.12775
G1 X118.854 Y113.626 E.1453
G1 X118.917 Y114.062 E.01461
G1 X118.917 Y117.152 E.1025
G1 X118.436 Y118.608 E.05086
G1 X114.381 Y118.608 E.13451
G1 X114.381 Y109.35 E.30709
M204 S10000
G1 X113.974 Y108.883 F42000
G1 F1842
M204 S6000
G1 X118.585 Y108.883 E.15296
G1 X119.257 Y113.568 E.15701
G1 X119.324 Y114.033 E.01557
G1 X119.324 Y117.217 E.10564
G1 X118.73 Y119.015 E.06279
G1 X113.974 Y119.015 E.15778
G1 X113.974 Y108.943 E.3341
M204 S10000
G1 X113.567 Y108.476 F42000
G1 F1842
M204 S6000
G1 X118.938 Y108.476 E.17817
G1 X119.66 Y113.511 E.16871
G1 X119.731 Y114.004 E.01653
G1 X119.731 Y117.283 E.10877
G1 X119.025 Y119.422 E.07472
G1 X113.567 Y119.422 E.18104
G1 X113.567 Y108.536 E.3611
M204 S250
G1 X113.175 Y108.084 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1842
M204 S5000
G1 X119.278 Y108.084 E.18753
G1 X120.048 Y113.455 E.16672
G1 X120.123 Y113.976 E.01617
G1 X120.123 Y117.346 E.10355
G1 X119.308 Y119.814 E.07986
G1 X113.175 Y119.814 E.18846
G1 X113.175 Y108.144 E.35859
; WIPE_START
G1 F3600
M204 S6000
G1 X115.175 Y108.124 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z9 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z9
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z9 F4000
            G39.3 S1
            G0 Z9 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X116.447 Y111.398 F42000
G1 Z8.6
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.60956
G1 F1842
M204 S6000
G1 X116.425 Y111.465 E.00324
; LINE_WIDTH: 0.565238
G1 X116.403 Y111.531 E.00298
; LINE_WIDTH: 0.520916
G1 X116.381 Y111.598 E.00273
; LINE_WIDTH: 0.476595
G1 X116.359 Y111.664 E.00248
; LINE_WIDTH: 0.432273
G1 X116.337 Y111.731 E.00222
; LINE_WIDTH: 0.387951
G1 X116.314 Y111.797 E.00197
; LINE_WIDTH: 0.387437
G1 X116.336 Y112.404 E.01704
; LINE_WIDTH: 0.430729
G1 X116.358 Y113.01 E.01918
; LINE_WIDTH: 0.474022
G1 X116.379 Y113.617 E.02133
; LINE_WIDTH: 0.536721
G1 X116.401 Y114.224 E.02443
G1 X116.401 Y116.588 E.09513
G1 X116.897 Y116.588 E.01996
G1 X116.895 Y114.189 E.09655
; LINE_WIDTH: 0.517314
G1 X116.83 Y113.585 E.02347
; LINE_WIDTH: 0.474022
G1 X116.765 Y112.981 E.02133
; LINE_WIDTH: 0.430729
G1 X116.7 Y112.378 E.01918
; LINE_WIDTH: 0.387437
G1 X116.636 Y111.774 E.01704
; LINE_WIDTH: 0.387951
G1 X116.609 Y111.72 E.00169
; LINE_WIDTH: 0.432273
G1 X116.582 Y111.667 E.00191
; LINE_WIDTH: 0.476595
G1 X116.555 Y111.613 E.00212
; LINE_WIDTH: 0.520916
G1 X116.528 Y111.559 E.00234
; LINE_WIDTH: 0.565238
G1 X116.501 Y111.506 E.00256
; LINE_WIDTH: 0.60956
G1 X116.474 Y111.452 E.00277
M204 S10000
G1 X115.964 Y110.873 F42000
; LINE_WIDTH: 0.41999
G1 F1842
M204 S6000
G1 X115.964 Y117.025 E.189
G1 X117.292 Y117.025 E.04078
G1 X117.334 Y116.873 E.00483
G1 X117.334 Y114.224 E.0814
G1 X116.86 Y110.873 E.10397
M73 P83 R3
G1 X116.024 Y110.873 E.02567
M204 S10000
G1 X115.587 Y110.496 F42000
G1 F1842
M204 S6000
G1 X115.587 Y117.402 E.21217
G1 X117.564 Y117.402 E.06074
G1 X117.711 Y116.873 E.01686
G1 X117.711 Y114.224 E.0814
G1 X117.187 Y110.496 E.11565
G1 X115.647 Y110.496 E.0473
; CHANGE_LAYER
; Z_HEIGHT: 8.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X117.187 Y110.496 E-.58501
G1 X117.251 Y110.952 E-.17499
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 44/79
; update layer progress
M73 L44
M991 S0 P43 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z9 I.395 J-1.151 P1  F42000
G1 X115.347 Y110.3 Z9
G1 Z8.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1775
M204 S6000
G1 X117.555 Y110.3 E.07322
G1 X118.107 Y114.148 E.12898
M73 P84 R3
G1 X118.141 Y114.384 E.00789
G1 X118.141 Y116.906 E.08368
G1 X117.876 Y117.709 E.02803
G1 X115.347 Y117.709 E.08387
G1 X115.347 Y110.36 E.24379
M204 S10000
G1 X114.94 Y109.892 F42000
G1 F1775
M204 S6000
G1 X117.908 Y109.892 E.09843
G1 X118.51 Y114.091 E.14068
G1 X118.548 Y114.355 E.00886
G1 X118.548 Y116.972 E.08681
G1 X118.17 Y118.116 E.03996
G1 X114.94 Y118.116 E.10713
G1 X114.94 Y109.952 E.2708
M204 S10000
G1 X114.533 Y109.485 F42000
G1 F1775
M204 S6000
G1 X118.26 Y109.485 E.12364
G1 X118.913 Y114.033 E.15239
G1 X118.955 Y114.326 E.00982
G1 X118.955 Y117.037 E.08995
G1 X118.464 Y118.523 E.0519
G1 X114.533 Y118.523 E.1304
G1 X114.533 Y109.545 E.2978
M204 S10000
G1 X114.126 Y109.078 F42000
G1 F1775
M204 S6000
G1 X118.613 Y109.078 E.14885
G1 X119.316 Y113.975 E.16409
G1 X119.362 Y114.297 E.01078
G1 X119.362 Y117.103 E.09308
G1 X118.758 Y118.93 E.06383
G1 X114.126 Y118.93 E.15366
G1 X114.126 Y109.138 E.32481
M204 S10000
G1 X113.719 Y108.671 F42000
G1 F1775
M204 S6000
G1 X118.966 Y108.671 E.17405
G1 X119.719 Y113.917 E.1758
G1 X119.769 Y114.268 E.01174
G1 X119.769 Y117.168 E.09622
G1 X119.053 Y119.337 E.07577
G1 X113.719 Y119.337 E.17693
G1 X113.719 Y108.731 E.35182
M204 S250
G1 X113.327 Y108.279 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1775
M204 S5000
G1 X119.306 Y108.279 E.18372
G1 X120.107 Y113.862 E.17328
G1 X120.161 Y114.24 E.01174
G1 X120.161 Y117.231 E.09193
G1 X119.336 Y119.729 E.08083
G1 X113.327 Y119.729 E.18465
G1 X113.327 Y108.339 E.34998
; WIPE_START
G1 F3600
M204 S6000
G1 X115.327 Y108.319 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z9.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z9.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z9.2 F4000
            G39.3 S1
            G0 Z9.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X116.599 Y112.458 F42000
G1 Z8.8
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.60956
G1 F1775
M204 S6000
G1 X116.577 Y112.524 E.00324
; LINE_WIDTH: 0.565238
G1 X116.555 Y112.591 E.00298
; LINE_WIDTH: 0.520916
G1 X116.533 Y112.657 E.00273
; LINE_WIDTH: 0.476595
G1 X116.511 Y112.724 E.00248
; LINE_WIDTH: 0.432273
G1 X116.489 Y112.79 E.00222
; LINE_WIDTH: 0.387951
G1 X116.466 Y112.857 E.00197
; LINE_WIDTH: 0.385139
G1 X116.486 Y113.399 E.01513
; LINE_WIDTH: 0.423835
G1 X116.505 Y113.941 E.01684
; LINE_WIDTH: 0.479825
G1 X116.524 Y114.484 E.01932
G1 X116.524 Y116.532 E.07292
G1 X116.963 Y116.532 E.01563
G1 X116.961 Y114.452 E.07403
; LINE_WIDTH: 0.462532
G1 X116.903 Y113.913 E.01855
; LINE_WIDTH: 0.423835
G1 X116.846 Y113.373 E.01684
; LINE_WIDTH: 0.385139
G1 X116.788 Y112.834 E.01513
; LINE_WIDTH: 0.387951
G1 X116.761 Y112.78 E.00169
; LINE_WIDTH: 0.432273
G1 X116.734 Y112.726 E.00191
; LINE_WIDTH: 0.476595
G1 X116.707 Y112.673 E.00212
; LINE_WIDTH: 0.520916
G1 X116.68 Y112.619 E.00234
; LINE_WIDTH: 0.565238
G1 X116.653 Y112.565 E.00256
; LINE_WIDTH: 0.60956
G1 X116.626 Y112.511 E.00277
M204 S10000
G1 X116.53 Y111.482 F42000
; LINE_WIDTH: 0.51567
G1 F1775
M204 S6000
G1 X116.552 Y111.787 E.01179
; LINE_WIDTH: 0.56209
G1 X116.573 Y112.093 E.01295
; LINE_WIDTH: 0.60851
G1 X116.595 Y112.398 E.01411
M204 S10000
G1 X116.116 Y111.069 F42000
; LINE_WIDTH: 0.41999
G1 F1775
M204 S6000
G1 X116.116 Y116.94 E.1804
G1 X117.32 Y116.94 E.03697
G1 X117.371 Y116.753 E.00596
G1 X117.365 Y114.395 E.07246
G1 X116.888 Y111.069 E.10324
G1 X116.176 Y111.069 E.02186
M204 S10000
G1 X115.739 Y110.692 F42000
G1 F1775
M204 S6000
G1 X115.739 Y117.317 E.20357
G1 X117.592 Y117.317 E.05693
G1 X117.749 Y116.753 E.01799
G1 X117.749 Y114.484 E.06972
G1 X117.215 Y110.692 E.11766
G1 X115.799 Y110.692 E.04349
; CHANGE_LAYER
; Z_HEIGHT: 9
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X117.215 Y110.692 E-.53788
G1 X117.296 Y111.27 E-.22212
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 45/79
; update layer progress
M73 L45
M991 S0 P44 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z9.2 I.482 J-1.117 P1  F42000
G1 X115.499 Y110.495 Z9.2
G1 Z9
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1708
M204 S6000
G1 X117.583 Y110.495 E.06911
G1 X118.165 Y114.555 E.13607
G1 X118.178 Y114.648 E.0031
G1 X118.178 Y116.792 E.07113
G1 X117.904 Y117.624 E.02907
G1 X115.499 Y117.624 E.07976
G1 X115.499 Y110.555 E.2345
M204 S10000
G1 X115.092 Y110.088 F42000
G1 F1708
M204 S6000
G1 X117.936 Y110.088 E.09432
G1 X118.568 Y114.497 E.14777
G1 X118.586 Y114.619 E.00407
G1 X118.586 Y116.857 E.07426
G1 X118.198 Y118.031 E.04101
G1 X115.092 Y118.031 E.10302
G1 X115.092 Y110.148 E.26151
M204 S10000
G1 X114.685 Y109.681 F42000
G1 F1708
M204 S6000
G1 X118.288 Y109.681 E.11953
G1 X118.971 Y114.439 E.15947
G1 X118.993 Y114.59 E.00503
G1 X118.993 Y116.923 E.0774
G1 X118.492 Y118.438 E.05294
G1 X114.685 Y118.438 E.12629
G1 X114.685 Y109.741 E.28852
M204 S10000
G1 X114.278 Y109.274 F42000
G1 F1708
M204 S6000
G1 X118.641 Y109.274 E.14473
G1 X119.374 Y114.382 E.17118
G1 X119.4 Y114.56 E.00599
G1 X119.4 Y116.988 E.08053
G1 X118.786 Y118.845 E.06487
G1 X114.278 Y118.845 E.14955
G1 X114.278 Y109.334 E.31552
M204 S10000
G1 X113.871 Y108.866 F42000
G1 F1708
M204 S6000
G1 X118.994 Y108.866 E.16994
G1 X119.777 Y114.324 E.18288
G1 X119.807 Y114.531 E.00696
G1 X119.807 Y117.054 E.08367
G1 X119.081 Y119.252 E.07681
G1 X113.871 Y119.252 E.17282
G1 X113.871 Y108.926 E.34253
M204 S250
G1 X113.479 Y108.474 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1708
M204 S5000
G1 X119.334 Y108.474 E.17991
G1 X120.165 Y114.268 E.17985
G1 X120.199 Y114.503 E.0073
G1 X120.199 Y117.117 E.0803
G1 X119.364 Y119.644 E.08179
G1 X113.479 Y119.644 E.18084
G1 X113.479 Y108.534 E.34138
; WIPE_START
G1 F3600
M204 S6000
G1 X115.479 Y108.514 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z9.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z9.4
M73 P85 R3
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z9.4 F4000
            G39.3 S1
            G0 Z9.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X116.751 Y113.518 F42000
G1 Z9
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.60956
G1 F1708
M204 S6000
G1 X116.729 Y113.584 E.00324
; LINE_WIDTH: 0.565238
G1 X116.707 Y113.65 E.00298
; LINE_WIDTH: 0.520916
G1 X116.685 Y113.717 E.00273
; LINE_WIDTH: 0.476595
G1 X116.663 Y113.783 E.00248
; LINE_WIDTH: 0.432273
G1 X116.641 Y113.85 E.00222
; LINE_WIDTH: 0.394717
G1 X116.618 Y113.916 E.00201
G1 X116.648 Y114.743 E.02371
; LINE_WIDTH: 0.42479
G1 X116.648 Y116.475 E.0539
G1 X117.03 Y116.475 E.01188
G1 X117.03 Y114.743 E.0539
; LINE_WIDTH: 0.41004
G1 X116.985 Y114.318 E.01278
; LINE_WIDTH: 0.38054
G1 X116.94 Y113.894 E.01175
; LINE_WIDTH: 0.387951
G1 X116.913 Y113.84 E.00169
; LINE_WIDTH: 0.432273
G1 X116.886 Y113.786 E.00191
; LINE_WIDTH: 0.476595
G1 X116.859 Y113.732 E.00212
; LINE_WIDTH: 0.520916
G1 X116.832 Y113.679 E.00234
; LINE_WIDTH: 0.565238
G1 X116.805 Y113.625 E.00256
; LINE_WIDTH: 0.60956
G1 X116.778 Y113.571 E.00277
M204 S10000
G1 X116.615 Y111.611 F42000
; LINE_WIDTH: 0.382277
G1 F1708
M204 S6000
G1 X116.637 Y111.919 E.00853
; LINE_WIDTH: 0.42763
G1 X116.659 Y112.226 E.00967
; LINE_WIDTH: 0.472984
G1 X116.681 Y112.534 E.01081
; LINE_WIDTH: 0.518337
G1 X116.703 Y112.842 E.01196
; LINE_WIDTH: 0.56369
G1 X116.725 Y113.15 E.0131
; LINE_WIDTH: 0.609044
G1 X116.747 Y113.458 E.01424
M204 S10000
G1 X116.269 Y111.264 F42000
; LINE_WIDTH: 0.41999
G1 F1708
M204 S6000
G1 X116.268 Y116.855 E.17179
G1 X117.348 Y116.855 E.03316
G1 X117.409 Y116.632 E.0071
G1 X117.409 Y114.743 E.05805
G2 X116.916 Y111.264 I-274.813 J37.186 E.10798
G1 X116.329 Y111.264 E.01805
M204 S10000
G1 X115.891 Y110.887 F42000
G1 F1708
M204 S6000
G1 X115.891 Y117.232 E.19496
G1 X117.62 Y117.232 E.05312
G1 X117.786 Y116.729 E.01628
G1 X117.786 Y114.743 E.06101
G2 X117.243 Y110.887 I-193.965 J25.369 E.11967
G1 X115.951 Y110.887 E.03968
; CHANGE_LAYER
; Z_HEIGHT: 9.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X117.243 Y110.887 E-.49076
G1 X117.342 Y111.588 E-.26924
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 46/79
; update layer progress
M73 L46
M991 S0 P45 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z9.4 I.571 J-1.075 P1  F42000
G1 X115.651 Y110.69 Z9.4
G1 Z9.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1630
M204 S6000
G1 X117.611 Y110.69 E.065
G1 X118.216 Y114.911 E.14147
G1 X118.216 Y116.677 E.05857
G1 X117.932 Y117.539 E.03011
G1 X115.651 Y117.539 E.07564
G1 X115.651 Y110.75 E.22521
M204 S10000
G1 X115.244 Y110.283 F42000
G1 F1630
M204 S6000
G1 X117.964 Y110.283 E.0902
G1 X118.623 Y114.882 E.15413
G1 X118.623 Y116.743 E.06171
G1 X118.226 Y117.946 E.04205
G1 X115.244 Y117.946 E.09891
G1 X115.244 Y110.343 E.25222
M204 S10000
G1 X114.837 Y109.876 F42000
G1 F1630
M204 S6000
G1 X118.316 Y109.876 E.11541
G1 X119.03 Y114.853 E.1668
G1 X119.03 Y116.808 E.06485
G1 X118.52 Y118.353 E.05398
G1 X114.837 Y118.353 E.12217
G1 X114.837 Y109.936 E.27923
M204 S10000
G1 X114.43 Y109.469 F42000
G1 F1630
M204 S6000
G1 X118.669 Y109.469 E.14062
G1 X119.432 Y114.788 E.17827
G1 X119.437 Y116.874 E.06917
G1 X118.814 Y118.76 E.06591
G1 X114.43 Y118.76 E.14544
G1 X114.43 Y109.529 E.30623
M204 S10000
G1 X114.023 Y109.062 F42000
G1 F1630
M204 S6000
G1 X119.022 Y109.062 E.16583
G1 X119.835 Y114.731 E.18997
G1 X119.845 Y116.939 E.07326
G1 X119.109 Y119.168 E.07785
G1 X114.023 Y119.168 E.1687
G1 X114.023 Y109.122 E.33324
M204 S250
G1 X113.631 Y108.67 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1630
M204 S5000
G1 X119.362 Y108.67 E.1761
G1 X120.223 Y114.675 E.18641
G1 X120.237 Y114.767 E.00287
G1 X120.237 Y117.002 E.06867
G1 X119.392 Y119.56 E.08276
G1 X113.631 Y119.56 E.17703
G1 X113.631 Y108.73 E.33278
; WIPE_START
G1 F3600
M204 S6000
G1 X115.631 Y108.709 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z9.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z9.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z9.6 F4000
            G39.3 S1
            G0 Z9.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X116.903 Y114.577 F42000
G1 Z9.2
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.609701
G1 F1630
M204 S6000
G1 X116.881 Y114.648 E.00343
; LINE_WIDTH: 0.565703
G1 X116.859 Y114.719 E.00317
; LINE_WIDTH: 0.521705
G1 X116.837 Y114.79 E.0029
; LINE_WIDTH: 0.477706
G1 X116.815 Y114.861 E.00263
; LINE_WIDTH: 0.433708
G1 X116.793 Y114.932 E.00237
; LINE_WIDTH: 0.368216
G1 X116.771 Y115.003 E.00197
G1 X116.771 Y116.419 E.03754
G1 X117.096 Y116.419 E.00861
G1 X117.096 Y115.003 E.03754
; LINE_WIDTH: 0.38971
G1 X117.068 Y114.941 E.00192
; LINE_WIDTH: 0.433708
G1 X117.04 Y114.879 E.00216
; LINE_WIDTH: 0.477706
G1 X117.012 Y114.817 E.00241
; LINE_WIDTH: 0.521705
G1 X116.984 Y114.755 E.00265
; LINE_WIDTH: 0.565703
G1 X116.956 Y114.694 E.00289
; LINE_WIDTH: 0.609701
G1 X116.928 Y114.632 E.00314
M204 S10000
G1 X116.785 Y112.913 F42000
; LINE_WIDTH: 0.417986
G1 F1630
M204 S6000
G1 X116.808 Y113.234 E.00983
; LINE_WIDTH: 0.465478
G1 X116.83 Y113.555 E.01108
; LINE_WIDTH: 0.51297
G1 X116.853 Y113.876 E.01232
; LINE_WIDTH: 0.560462
G1 X116.876 Y114.196 E.01356
; LINE_WIDTH: 0.607954
G1 X116.899 Y114.517 E.01481
M204 S10000
G1 X116.466 Y111.505 F42000
; LINE_WIDTH: 0.525738
G1 F1630
M204 S6000
G1 X116.48 Y112.01 E.01986
; LINE_WIDTH: 0.553373
G1 X116.494 Y112.514 E.02099
; LINE_WIDTH: 0.542657
G1 X116.47 Y112.647 E.00551
; LINE_WIDTH: 0.49359
G1 X116.445 Y112.78 E.00497
; LINE_WIDTH: 0.420364
G1 X116.42 Y112.913 E.00416
G1 X116.42 Y116.77 E.11863
G1 X117.376 Y116.77 E.02938
G1 X117.447 Y116.512 E.00824
G1 X117.447 Y115.003 E.04642
G2 X117.145 Y112.861 I-103.4 J13.487 E.06652
; LINE_WIDTH: 0.444524
G1 X117.102 Y112.733 E.00443
; LINE_WIDTH: 0.49359
G1 X117.059 Y112.605 E.00497
; LINE_WIDTH: 0.540016
G1 X117.016 Y112.477 E.00548
G1 X116.933 Y111.706 E.03139
; LINE_WIDTH: 0.51192
G1 X116.904 Y111.505 E.00777
G1 X116.526 Y111.505 E.01444
M204 S10000
G1 X116.043 Y111.082 F42000
; LINE_WIDTH: 0.41999
G1 F1630
M204 S6000
G1 X116.043 Y117.147 E.18636
G1 X117.648 Y117.147 E.04931
G1 X117.824 Y116.614 E.01725
G1 X117.824 Y115.003 E.04951
G2 X117.271 Y111.082 I-120.65 J15.027 E.12167
G1 X116.103 Y111.082 E.03587
; CHANGE_LAYER
; Z_HEIGHT: 9.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X117.271 Y111.082 E-.44365
G1 X117.387 Y111.906 E-.31635
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 47/79
; update layer progress
M73 L47
M991 S0 P46 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z9.6 I.659 J-1.023 P1  F42000
G1 X115.803 Y110.885 Z9.6
G1 Z9.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1546
M204 S6000
G1 X117.639 Y110.885 E.06088
G1 X118.245 Y115.109 E.14155
G1 X118.245 Y116.591 E.04916
G1 X117.96 Y117.454 E.03015
G1 X115.803 Y117.454 E.07153
G1 X115.803 Y110.945 E.21593
M204 S10000
G1 X115.396 Y110.478 F42000
G1 F1546
M204 S6000
G1 X117.992 Y110.478 E.08609
G1 X118.652 Y115.08 E.15422
G1 X118.652 Y116.657 E.0523
G1 X118.254 Y117.862 E.04209
G1 X115.396 Y117.862 E.09479
G1 X115.396 Y110.538 E.24293
M204 S10000
G1 X114.989 Y110.071 F42000
G1 F1546
M204 S6000
G1 X118.344 Y110.071 E.1113
G1 X119.059 Y115.051 E.16689
G1 X119.059 Y116.722 E.05543
G1 X118.548 Y118.269 E.05402
G1 X114.989 Y118.269 E.11806
G1 X114.989 Y110.131 E.26994
M204 S10000
G1 X114.582 Y109.664 F42000
G1 F1546
M204 S6000
G1 X118.697 Y109.664 E.13651
G1 X119.466 Y115.022 E.17956
G1 X119.466 Y116.788 E.05857
G1 X118.842 Y118.676 E.06595
G1 X114.582 Y118.676 E.14132
G1 X114.582 Y109.724 E.29695
M204 S10000
G1 X114.175 Y109.257 F42000
G1 F1546
M204 S6000
M73 P86 R3
G1 X119.05 Y109.257 E.16171
G1 X119.873 Y114.993 E.19223
G1 X119.873 Y116.853 E.06171
G1 X119.137 Y119.083 E.07789
G1 X114.175 Y119.083 E.16459
G1 X114.175 Y109.317 E.32395
M204 S250
G1 X113.783 Y108.865 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1546
M204 S5000
G1 X119.39 Y108.865 E.17229
G1 X120.265 Y114.965 E.18936
G1 X120.265 Y116.916 E.05995
G1 X119.42 Y119.475 E.08279
G1 X113.783 Y119.475 E.17322
G1 X113.783 Y108.925 E.32417
; WIPE_START
G1 F3600
M204 S6000
G1 X115.783 Y108.903 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z9.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z9.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z9.8 F4000
            G39.3 S1
            G0 Z9.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X116.937 Y113.973 F42000
G1 Z9.4
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41607
G1 F1546
M204 S6000
G1 X116.959 Y114.279 E.00932
; LINE_WIDTH: 0.45973
G1 X116.98 Y114.585 E.01042
; LINE_WIDTH: 0.50339
G1 X117.002 Y114.89 E.01151
; LINE_WIDTH: 0.563667
G1 X117.024 Y115.196 E.01301
G1 X117.024 Y116.174 E.04148
M204 S10000
G1 X116.585 Y111.667 F42000
; LINE_WIDTH: 0.44549
G1 F1546
M204 S6000
G1 X116.585 Y111.868 E.0066
; LINE_WIDTH: 0.465772
G1 X116.606 Y112.437 E.0196
; LINE_WIDTH: 0.506335
G1 X116.626 Y113.005 E.02148
; LINE_WIDTH: 0.546899
G1 X116.646 Y113.574 E.02336
; LINE_WIDTH: 0.542649
G1 X116.622 Y113.707 E.00551
; LINE_WIDTH: 0.493585
G1 X116.597 Y113.84 E.00497
; LINE_WIDTH: 0.420503
G1 X116.572 Y113.973 E.00416
G1 X116.572 Y116.685 E.08346
G1 X117.404 Y116.685 E.02557
G1 X117.476 Y116.426 E.00828
G1 X117.476 Y115.196 E.03783
G1 X117.297 Y113.921 E.03962
; LINE_WIDTH: 0.444522
G1 X117.254 Y113.793 E.00443
; LINE_WIDTH: 0.493585
G1 X117.211 Y113.665 E.00497
; LINE_WIDTH: 0.542649
G1 X117.168 Y113.537 E.00551
; LINE_WIDTH: 0.546899
G1 X117.107 Y112.971 E.02336
; LINE_WIDTH: 0.506335
G1 X117.046 Y112.405 E.02148
; LINE_WIDTH: 0.456384
G2 X116.961 Y111.667 I-10.374 J.826 E.02505
G1 X116.645 Y111.667 E.01064
M204 S10000
G1 X116.195 Y111.277 F42000
; LINE_WIDTH: 0.41999
G1 F1546
M204 S6000
G1 X116.195 Y117.062 E.17776
G1 X117.676 Y117.062 E.0455
G1 X117.853 Y116.528 E.01729
G1 X117.853 Y115.196 E.04093
G1 X117.299 Y111.277 E.12161
G1 X116.255 Y111.277 E.03206
; CHANGE_LAYER
; Z_HEIGHT: 9.6
; LAYER_HEIGHT: 0.200001
; WIPE_START
G1 F9547.299
G1 X117.299 Y111.277 E-.39652
G1 X117.433 Y112.224 E-.36348
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 48/79
; update layer progress
M73 L48
M991 S0 P47 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z9.8 I.745 J-.962 P1  F42000
G1 X115.955 Y111.08 Z9.8
G1 Z9.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1482
M204 S6000
G1 X117.667 Y111.08 E.05677
G1 X118.245 Y115.109 E.13501
G1 X118.245 Y116.591 E.04916
G1 X117.988 Y117.37 E.02719
G1 X115.955 Y117.37 E.06742
G1 X115.955 Y111.14 E.20664
M204 S10000
G1 X115.548 Y110.673 F42000
G1 F1482
M204 S6000
G1 X118.02 Y110.673 E.08198
G1 X118.652 Y115.08 E.14768
G1 X118.652 Y116.657 E.0523
G1 X118.282 Y117.777 E.03913
G1 X115.548 Y117.777 E.09068
G1 X115.548 Y110.733 E.23364
M204 S10000
G1 X115.141 Y110.266 F42000
G1 F1482
M204 S6000
G1 X118.372 Y110.266 E.10719
G1 X119.059 Y115.051 E.16035
G1 X119.059 Y116.722 E.05543
G1 X118.576 Y118.184 E.05106
G1 X115.141 Y118.184 E.11395
G1 X115.141 Y110.326 E.26065
M204 S10000
G1 X114.734 Y109.859 F42000
G1 F1482
M204 S6000
G1 X118.725 Y109.859 E.13239
G1 X119.466 Y115.022 E.17302
G1 X119.466 Y116.788 E.05857
G1 X118.87 Y118.591 E.06299
G1 X114.734 Y118.591 E.13721
G1 X114.734 Y109.919 E.28766
M204 S10000
G1 X114.327 Y109.452 F42000
G1 F1482
M204 S6000
G1 X119.078 Y109.452 E.1576
G1 X119.873 Y114.993 E.18568
G1 X119.873 Y116.853 E.06171
G1 X119.165 Y118.998 E.07492
G1 X114.327 Y118.998 E.16048
G1 X114.327 Y109.512 E.31466
M204 S250
G1 X113.935 Y109.06 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1482
M204 S5000
G1 X119.418 Y109.06 E.16848
G1 X120.265 Y114.965 E.1833
G1 X120.265 Y116.916 E.05995
G1 X119.448 Y119.39 E.08005
G1 X113.935 Y119.39 E.1694
G1 X113.935 Y109.12 E.31557
; WIPE_START
G1 F3600
M204 S6000
G1 X115.935 Y109.098 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z10 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z10
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z10 F4000
            G39.3 S1
            G0 Z10 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.089 Y115.032 F42000
G1 Z9.6
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.415303
G1 F1482
M204 S6000
G1 X117.1 Y116.165 E.03438
M204 S10000
G1 X116.704 Y111.829 F42000
; LINE_WIDTH: 0.37907
G1 F1482
M204 S6000
G1 X116.704 Y111.997 E.0046
; LINE_WIDTH: 0.402585
G1 X116.728 Y112.656 E.01933
; LINE_WIDTH: 0.449615
G1 X116.751 Y113.315 E.02185
; LINE_WIDTH: 0.496645
G1 X116.775 Y113.974 E.02438
; LINE_WIDTH: 0.543675
G1 X116.798 Y114.633 E.02691
; LINE_WIDTH: 0.542657
G1 X116.774 Y114.819 E.00764
; LINE_WIDTH: 0.49359
G1 X116.749 Y115.005 E.00689
; LINE_WIDTH: 0.42116
G1 X116.724 Y115.191 E.00578
G1 X116.724 Y116.601 E.04345
G1 X117.432 Y116.601 E.02179
G1 X117.476 Y116.442 E.00507
G1 X117.476 Y115.191 E.03856
G1 X117.449 Y114.981 E.00653
; LINE_WIDTH: 0.444524
G1 X117.406 Y114.852 E.00443
; LINE_WIDTH: 0.49359
G1 X117.363 Y114.724 E.00497
; LINE_WIDTH: 0.542657
G1 X117.32 Y114.596 E.00551
; LINE_WIDTH: 0.543675
G1 X117.249 Y113.94 E.02691
; LINE_WIDTH: 0.496645
G1 X117.179 Y113.285 E.02438
; LINE_WIDTH: 0.449615
G1 X117.109 Y112.629 E.02185
; LINE_WIDTH: 0.393715
G2 X117.018 Y111.829 I-11.271 J.877 E.02302
G1 X116.764 Y111.829 E.00725
M204 S10000
G1 X116.347 Y111.472 F42000
; LINE_WIDTH: 0.41999
G1 F1482
M204 S6000
G1 X116.347 Y116.978 E.16915
G1 X117.704 Y116.978 E.04169
G1 X117.853 Y116.442 E.01707
G1 X117.853 Y115.191 E.03845
G2 X117.327 Y111.472 I-162.618 J21.094 E.11539
G1 X116.407 Y111.472 E.02825
; CHANGE_LAYER
; Z_HEIGHT: 9.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X117.327 Y111.472 E-.34941
G1 X117.478 Y112.542 E-.41059
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 49/79
; update layer progress
M73 L49
M991 S0 P48 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z10 I.826 J-.894 P1  F42000
G1 X116.107 Y111.276 Z10
G1 Z9.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1406
M204 S6000
G1 X117.695 Y111.276 E.05266
G1 X118.245 Y115.109 E.12847
G1 X118.245 Y116.591 E.04916
G1 X118.016 Y117.285 E.02423
G1 X116.107 Y117.285 E.0633
G1 X116.107 Y111.336 E.19735
M204 S10000
G1 X115.7 Y110.868 F42000
G1 F1406
M204 S6000
G1 X118.048 Y110.868 E.07786
G1 X118.652 Y115.08 E.14114
G1 X118.652 Y116.657 E.0523
G1 X118.31 Y117.692 E.03616
G1 X115.7 Y117.692 E.08657
G1 X115.7 Y110.928 E.22436
M204 S10000
G1 X115.293 Y110.461 F42000
G1 F1406
M204 S6000
G1 X118.4 Y110.461 E.10307
G1 X119.059 Y115.051 E.15381
G1 X119.059 Y116.722 E.05543
G1 X118.604 Y118.099 E.0481
G1 X115.293 Y118.099 E.10983
G1 X115.293 Y110.521 E.25136
M204 S10000
G1 X114.886 Y110.054 F42000
G1 F1406
M204 S6000
G1 X118.753 Y110.054 E.12828
G1 X119.466 Y115.022 E.16647
M73 P87 R3
G1 X119.466 Y116.788 E.05857
G1 X118.898 Y118.506 E.06003
G1 X114.886 Y118.506 E.1331
G1 X114.886 Y110.114 E.27837
M204 S10000
G1 X114.479 Y109.647 F42000
G1 F1406
M204 S6000
G1 X119.106 Y109.647 E.15349
G1 X119.873 Y114.993 E.17914
G1 X119.873 Y116.853 E.06171
G1 X119.193 Y118.913 E.07196
G1 X114.479 Y118.913 E.15636
G1 X114.479 Y109.707 E.30538
M204 S250
G1 X114.087 Y109.255 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1406
M204 S5000
G1 X119.446 Y109.255 E.16467
G1 X120.265 Y114.965 E.17724
G1 X120.265 Y116.916 E.05995
G1 X119.476 Y119.305 E.07731
G1 X114.087 Y119.305 E.16559
G1 X114.087 Y109.315 E.30697
; WIPE_START
G1 F3600
M204 S6000
G1 X116.087 Y109.293 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z10.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z10.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z10.2 F4000
            G39.3 S1
            G0 Z10.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X116.499 Y111.668 F42000
G1 Z9.8
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.41999
G1 F1406
M204 S6000
G1 X116.499 Y116.893 E.16055
G1 X117.732 Y116.893 E.03788
G1 X117.853 Y116.458 E.01385
G1 X117.846 Y115.089 E.04206
G1 X117.355 Y111.668 E.10621
G1 X116.559 Y111.668 E.02444
M204 S10000
G1 X116.958 Y112.126 F42000
; LINE_WIDTH: 0.60704
G1 F1406
M204 S6000
G1 X116.978 Y112.412 E.01318
M204 S10000
G1 X116.982 Y112.472 F42000
; LINE_WIDTH: 0.60956
G1 F1406
M204 S6000
G1 X116.96 Y112.538 E.00324
; LINE_WIDTH: 0.565238
G1 X116.938 Y112.605 E.00298
; LINE_WIDTH: 0.520916
G1 X116.916 Y112.671 E.00273
; LINE_WIDTH: 0.476595
G1 X116.894 Y112.738 E.00248
; LINE_WIDTH: 0.432273
G1 X116.872 Y112.804 E.00222
; LINE_WIDTH: 0.387951
G1 X116.849 Y112.871 E.00197
; LINE_WIDTH: 0.386438
G1 X116.87 Y113.449 E.01621
; LINE_WIDTH: 0.427733
G1 X116.891 Y114.028 E.01816
; LINE_WIDTH: 0.469028
G1 X116.911 Y114.607 E.02011
; LINE_WIDTH: 0.527693
G3 X116.932 Y116.46 I-25.959 J1.216 E.07324
G1 X117.418 Y116.458 E.0192
G2 X117.418 Y115.151 I-93.169 J-.612 E.05165
; LINE_WIDTH: 0.510323
G1 X117.356 Y114.575 E.02205
; LINE_WIDTH: 0.469028
G1 X117.294 Y113.999 E.02011
; LINE_WIDTH: 0.427733
G1 X117.232 Y113.424 E.01816
; LINE_WIDTH: 0.386438
G1 X117.171 Y112.848 E.01621
; LINE_WIDTH: 0.387951
G1 X117.144 Y112.794 E.00169
; LINE_WIDTH: 0.432273
G1 X117.117 Y112.74 E.00191
; LINE_WIDTH: 0.476595
G1 X117.09 Y112.687 E.00212
; LINE_WIDTH: 0.520916
G1 X117.063 Y112.633 E.00234
; LINE_WIDTH: 0.565238
G1 X117.036 Y112.579 E.00256
; LINE_WIDTH: 0.60956
G1 X117.009 Y112.525 E.00277
; CHANGE_LAYER
; Z_HEIGHT: 10
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F6353.249
G1 X117.036 Y112.579 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 50/79
; update layer progress
M73 L50
M991 S0 P49 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z10.2 I.997 J-.698 P1  F42000
G1 X116.259 Y111.471 Z10.2
G1 Z10
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1343
M204 S6000
G1 X117.723 Y111.471 E.04854
G1 X118.245 Y115.109 E.12193
G1 X118.245 Y116.591 E.04916
G1 X118.044 Y117.2 E.02127
G1 X116.259 Y117.2 E.05919
G1 X116.259 Y111.531 E.18806
M204 S10000
G1 X115.852 Y111.064 F42000
G1 F1343
M204 S6000
G1 X118.076 Y111.064 E.07375
G1 X118.652 Y115.08 E.1346
G1 X118.652 Y116.657 E.0523
G1 X118.338 Y117.607 E.0332
G1 X115.852 Y117.607 E.08245
G1 X115.852 Y111.124 E.21507
M204 S10000
G1 X115.445 Y110.657 F42000
G1 F1343
M204 S6000
G1 X118.428 Y110.657 E.09896
G1 X119.059 Y115.051 E.14727
G1 X119.059 Y116.722 E.05543
G1 X118.632 Y118.014 E.04513
G1 X115.445 Y118.014 E.10572
G1 X115.445 Y110.717 E.24207
M204 S10000
G1 X115.038 Y110.25 F42000
G1 F1343
M204 S6000
G1 X118.781 Y110.25 E.12417
G1 X119.466 Y115.022 E.15993
G1 X119.466 Y116.788 E.05857
G1 X118.926 Y118.421 E.05707
G1 X115.038 Y118.421 E.12898
G1 X115.038 Y110.31 E.26908
M204 S10000
G1 X114.631 Y109.842 F42000
G1 F1343
M204 S6000
G1 X119.134 Y109.842 E.14937
G1 X119.873 Y114.993 E.1726
G1 X119.873 Y116.853 E.06171
G1 X119.221 Y118.828 E.069
G1 X114.631 Y118.828 E.15225
G1 X114.631 Y109.902 E.29609
M204 S250
G1 X114.239 Y109.45 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1343
M204 S5000
G1 X119.474 Y109.45 E.16086
G1 X120.265 Y114.965 E.17118
G1 X120.265 Y116.916 E.05995
G1 X119.504 Y119.22 E.07456
G1 X114.239 Y119.22 E.16178
G1 X114.239 Y109.51 E.29836
; WIPE_START
G1 F3600
M204 S6000
G1 X116.239 Y109.487 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z10.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z10.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z10.4 F4000
            G39.3 S1
            G0 Z10.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.134 Y113.531 F42000
G1 Z10
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.60956
G1 F1343
M204 S6000
G1 X117.112 Y113.598 E.00324
; LINE_WIDTH: 0.565238
G1 X117.09 Y113.664 E.00298
; LINE_WIDTH: 0.520916
G1 X117.068 Y113.731 E.00273
; LINE_WIDTH: 0.476595
G1 X117.046 Y113.797 E.00248
; LINE_WIDTH: 0.432273
G1 X117.024 Y113.864 E.00222
; LINE_WIDTH: 0.409195
G1 X117.001 Y113.93 E.00209
G1 X117.046 Y115.18 E.03732
; LINE_WIDTH: 0.454975
G1 X117.046 Y116.413 E.04141
G1 X117.458 Y116.413 E.01384
G1 X117.456 Y115.151 E.0424
; LINE_WIDTH: 0.432683
G1 X117.389 Y114.529 E.01986
; LINE_WIDTH: 0.388088
G1 X117.323 Y113.907 E.01759
; LINE_WIDTH: 0.387951
M73 P87 R2
G1 X117.296 Y113.854 E.00169
; LINE_WIDTH: 0.432273
G1 X117.269 Y113.8 E.00191
; LINE_WIDTH: 0.476595
G1 X117.242 Y113.746 E.00212
; LINE_WIDTH: 0.520916
G1 X117.215 Y113.692 E.00234
; LINE_WIDTH: 0.565238
G1 X117.188 Y113.639 E.00256
; LINE_WIDTH: 0.60956
G1 X117.161 Y113.585 E.00277
M204 S10000
G1 X117.043 Y112.255 F42000
; LINE_WIDTH: 0.472295
M73 P88 R2
G1 F1343
M204 S6000
G1 X117.065 Y112.559 E.01067
; LINE_WIDTH: 0.517845
G1 X117.087 Y112.863 E.0118
; LINE_WIDTH: 0.563395
G1 X117.108 Y113.167 E.01293
; LINE_WIDTH: 0.608945
G1 X117.13 Y113.471 E.01407
M204 S10000
G1 X116.651 Y111.863 F42000
; LINE_WIDTH: 0.41999
G1 F1343
M204 S6000
G1 X116.651 Y116.808 E.15195
G1 X117.76 Y116.808 E.03407
G1 X117.853 Y116.475 E.01063
G1 X117.847 Y115.095 E.0424
G1 X117.383 Y111.863 E.10032
G1 X116.711 Y111.863 E.02063
; CHANGE_LAYER
; Z_HEIGHT: 10.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9547.299
G1 X117.383 Y111.863 E-.25516
G1 X117.572 Y113.178 E-.50484
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 51/79
; update layer progress
M73 L51
M991 S0 P50 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z10.4 I.965 J-.741 P1  F42000
G1 X116.411 Y111.666 Z10.4
G1 Z10.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1278
M204 S6000
G1 X117.751 Y111.666 E.04443
G1 X118.245 Y115.109 E.11539
G1 X118.245 Y116.591 E.04916
G1 X118.072 Y117.115 E.0183
G1 X116.411 Y117.115 E.05508
G1 X116.411 Y111.726 E.17877
M204 S10000
G1 X116.004 Y111.259 F42000
G1 F1278
M204 S6000
G1 X118.104 Y111.259 E.06964
G1 X118.652 Y115.08 E.12806
G1 X118.652 Y116.657 E.0523
G1 X118.366 Y117.522 E.03024
G1 X116.004 Y117.522 E.07834
G1 X116.004 Y111.319 E.20578
M204 S10000
G1 X115.597 Y110.852 F42000
G1 F1278
M204 S6000
G1 X118.456 Y110.852 E.09485
G1 X119.059 Y115.051 E.14072
G1 X119.059 Y116.722 E.05543
G1 X118.66 Y117.929 E.04217
G1 X115.597 Y117.929 E.10161
G1 X115.597 Y110.912 E.23279
M204 S10000
G1 X115.19 Y110.445 F42000
G1 F1278
M204 S6000
G1 X118.809 Y110.445 E.12005
G1 X119.466 Y115.022 E.15339
G1 X119.466 Y116.788 E.05857
G1 X118.954 Y118.336 E.0541
G1 X115.19 Y118.336 E.12487
G1 X115.19 Y110.505 E.25979
M204 S10000
G1 X114.783 Y110.038 F42000
G1 F1278
M204 S6000
G1 X119.162 Y110.038 E.14526
G1 X119.873 Y114.993 E.16606
G1 X119.873 Y116.853 E.06171
G1 X119.249 Y118.744 E.06604
G1 X114.783 Y118.744 E.14814
G1 X114.783 Y110.098 E.2868
M204 S250
G1 X114.391 Y109.646 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1278
M204 S5000
G1 X119.502 Y109.646 E.15705
G1 X120.265 Y114.965 E.16512
G1 X120.265 Y116.916 E.05995
G1 X119.532 Y119.136 E.07182
G1 X114.391 Y119.136 E.15797
G1 X114.391 Y109.706 E.28976
; WIPE_START
G1 F3600
M204 S6000
G1 X116.391 Y109.682 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z10.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z10.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z10.6 F4000
            G39.3 S1
            G0 Z10.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.286 Y114.591 F42000
G1 Z10.2
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.60954
G1 F1278
M204 S6000
G1 X117.264 Y114.658 E.00324
; LINE_WIDTH: 0.56522
G1 X117.242 Y114.724 E.00298
; LINE_WIDTH: 0.5209
G1 X117.22 Y114.79 E.00273
; LINE_WIDTH: 0.47658
G1 X117.198 Y114.857 E.00248
; LINE_WIDTH: 0.43226
G1 X117.176 Y114.923 E.00222
; LINE_WIDTH: 0.378353
G1 X117.153 Y114.99 E.00192
G3 X117.16 Y116.367 I-19.311 J.781 E.03764
G1 X117.496 Y116.367 E.00919
G1 X117.496 Y115.175 E.03258
G1 X117.475 Y114.967 E.0057
; LINE_WIDTH: 0.38794
G1 X117.448 Y114.913 E.00169
; LINE_WIDTH: 0.43226
G1 X117.421 Y114.86 E.00191
; LINE_WIDTH: 0.47658
G1 X117.394 Y114.806 E.00212
; LINE_WIDTH: 0.5209
G1 X117.367 Y114.752 E.00234
; LINE_WIDTH: 0.56522
G1 X117.34 Y114.698 E.00256
; LINE_WIDTH: 0.60954
G1 X117.313 Y114.645 E.00277
M204 S10000
G1 X117.168 Y112.927 F42000
; LINE_WIDTH: 0.418004
G1 F1278
M204 S6000
G1 X117.191 Y113.248 E.00983
; LINE_WIDTH: 0.465492
G1 X117.213 Y113.569 E.01107
; LINE_WIDTH: 0.51298
G1 X117.236 Y113.89 E.01232
; LINE_WIDTH: 0.560468
G1 X117.259 Y114.21 E.01356
; LINE_WIDTH: 0.607956
G1 X117.282 Y114.531 E.01481
M204 S10000
G1 X116.872 Y112.126 F42000
; LINE_WIDTH: 0.562025
G1 F1278
M204 S6000
G1 X116.877 Y112.528 E.01699
; LINE_WIDTH: 0.542657
G1 X116.852 Y112.661 E.00551
; LINE_WIDTH: 0.49359
G1 X116.828 Y112.794 E.00497
; LINE_WIDTH: 0.420368
G1 X116.803 Y112.927 E.00416
G1 X116.803 Y116.723 E.11676
G1 X117.788 Y116.723 E.03029
G1 X117.853 Y116.491 E.00742
G1 X117.853 Y115.175 E.04048
G2 X117.528 Y112.875 I-143.343 J19.056 E.07142
; LINE_WIDTH: 0.442802
G1 X117.48 Y112.699 E.00595
; LINE_WIDTH: 0.488425
G1 X117.432 Y112.523 E.00663
; LINE_WIDTH: 0.55181
G3 X117.352 Y112.126 I1.536 J-.516 E.01682
G1 X116.932 Y112.126 E.0174
; CHANGE_LAYER
; Z_HEIGHT: 10.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F7074.219
G1 X117.352 Y112.126 E-.38659
G1 X117.383 Y112.347 E-.20516
G1 X117.432 Y112.523 E-.16824
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 52/79
; update layer progress
M73 L52
M991 S0 P51 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z10.6 I.738 J-.968 P1  F42000
G1 X116.563 Y111.861 Z10.6
G1 Z10.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X117.779 Y111.861 E.04032
G1 X118.245 Y115.109 E.10885
G1 X118.245 Y116.591 E.04916
G1 X118.1 Y117.03 E.01534
G1 X116.563 Y117.03 E.05096
G1 X116.563 Y111.921 E.16949
M204 S10000
G1 X116.156 Y111.454 F42000
G1 F1200
M204 S6000
G1 X118.132 Y111.454 E.06552
G1 X118.652 Y115.08 E.12152
G1 X118.652 Y116.657 E.0523
G1 X118.394 Y117.438 E.02728
G1 X116.156 Y117.438 E.07423
G1 X116.156 Y111.514 E.19649
M204 S10000
G1 X115.749 Y111.047 F42000
G1 F1200
M204 S6000
G1 X118.484 Y111.047 E.09073
G1 X119.059 Y115.051 E.13418
G1 X119.059 Y116.722 E.05543
G1 X118.688 Y117.845 E.03921
G1 X115.749 Y117.845 E.09749
G1 X115.749 Y111.107 E.2235
M204 S10000
G1 X115.342 Y110.64 F42000
G1 F1200
M204 S6000
G1 X118.837 Y110.64 E.11594
G1 X119.466 Y115.022 E.14685
G1 X119.466 Y116.788 E.05857
G1 X118.982 Y118.252 E.05114
G1 X115.342 Y118.252 E.12076
G1 X115.342 Y110.7 E.2505
M204 S10000
G1 X114.935 Y110.233 F42000
G1 F1200
M204 S6000
G1 X119.19 Y110.233 E.14115
G1 X119.873 Y114.993 E.15952
G1 X119.873 Y116.853 E.06171
G1 X119.277 Y118.659 E.06307
G1 X114.935 Y118.659 E.14402
G1 X114.935 Y110.293 E.27751
M204 S250
G1 X114.543 Y109.841 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.53 Y109.841 E.15324
G1 X120.265 Y114.965 E.15906
G1 X120.265 Y116.916 E.05995
G1 X119.56 Y119.051 E.06907
G1 X114.543 Y119.051 E.15416
G1 X114.543 Y109.901 E.28115
; WIPE_START
G1 F3600
M204 S6000
G1 X116.543 Y109.877 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z10.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z10.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
M73 P89 R2
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z10.8 F4000
            G39.3 S1
            G0 Z10.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X116.991 Y112.288 F42000
G1 Z10.4
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.49044
G1 F1200
M204 S6000
G1 X116.991 Y112.512 E.00816
; LINE_WIDTH: 0.509628
G1 X117.01 Y113.05 E.02046
; LINE_WIDTH: 0.548003
G1 X117.029 Y113.588 E.02215
; LINE_WIDTH: 0.542657
G1 X117.004 Y113.721 E.00551
; LINE_WIDTH: 0.49359
G1 X116.98 Y113.854 E.00497
; LINE_WIDTH: 0.420511
G1 X116.955 Y113.987 E.00416
G1 X116.955 Y116.638 E.08159
G1 X117.816 Y116.638 E.02649
G1 X117.853 Y116.507 E.00419
G1 X117.853 Y115.169 E.04117
G1 X117.68 Y113.935 E.03834
; LINE_WIDTH: 0.444524
G1 X117.637 Y113.807 E.00443
; LINE_WIDTH: 0.49359
G1 X117.594 Y113.679 E.00497
; LINE_WIDTH: 0.530361
G1 X117.551 Y113.55 E.00537
G1 X117.436 Y112.48 E.04275
; LINE_WIDTH: 0.49044
G1 X117.408 Y112.288 E.00707
G1 X117.051 Y112.288 E.01304
M204 S10000
G1 X117.32 Y113.987 F42000
; LINE_WIDTH: 0.415355
G1 F1200
M204 S6000
G1 X117.341 Y114.282 E.00899
; LINE_WIDTH: 0.457545
G1 X117.362 Y114.578 E.01001
; LINE_WIDTH: 0.499735
G1 X117.383 Y114.874 E.01103
; LINE_WIDTH: 0.558047
G1 X117.404 Y115.169 E.01244
G1 X117.404 Y116.13 E.04032
; CHANGE_LAYER
; Z_HEIGHT: 10.6
; LAYER_HEIGHT: 0.200001
; WIPE_START
G1 F6988.579
G1 X117.404 Y115.169 E-.5808
G1 X117.383 Y114.874 E-.1792
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 53/79
; update layer progress
M73 L53
M991 S0 P52 ;notify layer change
M106 S204
; OBJECT_ID: 105
M204 S10000
G17
G3 Z10.8 I1.184 J-.281 P1  F42000
G1 X116.715 Y112.056 Z10.8
G1 Z10.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X117.807 Y112.056 E.0362
G1 X118.245 Y115.109 E.10231
G1 X118.245 Y116.591 E.04916
G1 X118.128 Y116.946 E.01238
G1 X116.715 Y116.946 E.04685
G1 X116.715 Y112.116 E.1602
M204 S10000
G1 X116.308 Y111.649 F42000
G1 F1200
M204 S6000
G1 X118.16 Y111.649 E.06141
G1 X118.652 Y115.08 E.11497
G1 X118.652 Y116.657 E.0523
G1 X118.422 Y117.353 E.02431
G1 X116.308 Y117.353 E.07011
G1 X116.308 Y111.709 E.1872
M204 S10000
G1 X115.901 Y111.242 F42000
G1 F1200
M204 S6000
G1 X118.512 Y111.242 E.08662
G1 X119.059 Y115.051 E.12764
G1 X119.059 Y116.722 E.05543
G1 X118.716 Y117.76 E.03625
G1 X115.901 Y117.76 E.09338
G1 X115.901 Y111.302 E.21421
M204 S10000
G1 X115.494 Y110.835 F42000
G1 F1200
M204 S6000
G1 X118.865 Y110.835 E.11183
G1 X119.466 Y115.022 E.14031
G1 X119.466 Y116.788 E.05857
G1 X119.01 Y118.167 E.04818
G1 X115.494 Y118.167 E.11664
G1 X115.494 Y110.895 E.24122
M204 S10000
G1 X115.087 Y110.428 F42000
G1 F1200
M204 S6000
G1 X119.218 Y110.428 E.13703
G1 X119.873 Y114.993 E.15298
G1 X119.873 Y116.853 E.06171
G1 X119.305 Y118.574 E.06011
G1 X115.087 Y118.574 E.13991
G1 X115.087 Y110.488 E.26822
M204 S250
G1 X114.695 Y110.036 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.558 Y110.036 E.14943
G1 X120.265 Y114.965 E.153
G1 X120.265 Y116.916 E.05995
G1 X119.588 Y118.966 E.06633
G1 X114.695 Y118.966 E.15035
G1 X114.695 Y110.096 E.27255
; WIPE_START
G1 F3600
M204 S6000
G1 X116.695 Y110.071 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z11 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z11
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z11 F4000
            G39.3 S1
            G0 Z11 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.109 Y112.45 F42000
G1 Z10.6
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.42402
G1 F1200
M204 S6000
G1 X117.109 Y112.641 E.00592
; LINE_WIDTH: 0.44788
G1 X117.133 Y113.31 E.02208
; LINE_WIDTH: 0.4956
G1 X117.157 Y113.979 E.02469
; LINE_WIDTH: 0.54332
G1 X117.181 Y114.647 E.02729
; LINE_WIDTH: 0.542649
G1 X117.156 Y114.819 E.00708
; LINE_WIDTH: 0.493585
G1 X117.132 Y114.992 E.00639
; LINE_WIDTH: 0.421095
G1 X117.107 Y115.164 E.00536
G1 X117.107 Y116.554 E.04283
G1 X117.844 Y116.554 E.02271
G2 X117.853 Y115.164 I-30.893 J-.881 E.04283
G1 X117.832 Y114.995 E.00525
; LINE_WIDTH: 0.444522
G1 X117.789 Y114.866 E.00443
; LINE_WIDTH: 0.493585
G1 X117.746 Y114.738 E.00497
; LINE_WIDTH: 0.542649
G1 X117.703 Y114.61 E.00551
; LINE_WIDTH: 0.54332
G1 X117.631 Y113.945 E.02729
; LINE_WIDTH: 0.4956
G1 X117.56 Y113.279 E.02469
; LINE_WIDTH: 0.438149
G2 X117.465 Y112.45 I-11.667 J.914 E.02687
G1 X117.169 Y112.45 E.00952
M204 S10000
G1 X117.472 Y115.046 F42000
; LINE_WIDTH: 0.410101
G1 F1200
M204 S6000
G1 X117.48 Y116.121 E.03216
; CHANGE_LAYER
; Z_HEIGHT: 10.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9804.433
G1 X117.472 Y115.046 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 54/79
; update layer progress
M73 L54
M991 S0 P53 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z11 I1.189 J-.257 P1  F42000
G1 X116.867 Y112.252 Z11
G1 Z10.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X117.835 Y112.252 E.03209
G1 X118.245 Y115.109 E.09576
G1 X118.245 Y116.591 E.04916
G1 X118.156 Y116.861 E.00942
G1 X116.867 Y116.861 E.04273
G1 X116.867 Y112.312 E.15091
M204 S10000
G1 X116.46 Y111.844 F42000
G1 F1200
M204 S6000
G1 X118.188 Y111.844 E.0573
G1 X118.652 Y115.08 E.10843
G1 X118.652 Y116.657 E.0523
G1 X118.45 Y117.268 E.02135
G1 X116.46 Y117.268 E.066
G1 X116.46 Y111.904 E.17792
M204 S10000
G1 X116.053 Y111.437 F42000
G1 F1200
M204 S6000
G1 X118.54 Y111.437 E.08251
G1 X119.059 Y115.051 E.1211
G1 X119.059 Y116.722 E.05543
G1 X118.744 Y117.675 E.03328
G1 X116.053 Y117.675 E.08927
G1 X116.053 Y111.497 E.20492
M204 S10000
G1 X115.646 Y111.03 F42000
G1 F1200
M204 S6000
G1 X118.893 Y111.03 E.10771
G1 X119.466 Y115.022 E.13377
G1 X119.466 Y116.788 E.05857
G1 X119.038 Y118.082 E.04522
G1 X115.646 Y118.082 E.11253
G1 X115.646 Y111.09 E.23193
M204 S10000
G1 X115.239 Y110.623 F42000
G1 F1200
M204 S6000
G1 X119.246 Y110.623 E.13292
G1 X119.873 Y114.993 E.14644
G1 X119.873 Y116.853 E.06171
G1 X119.333 Y118.489 E.05715
G1 X115.239 Y118.489 E.1358
G1 X115.239 Y110.683 E.25894
M204 S250
G1 X114.847 Y110.231 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.586 Y110.231 E.14562
G1 X120.265 Y114.965 E.14695
G1 X120.265 Y116.916 E.05995
G1 X119.616 Y118.881 E.06359
G1 X114.847 Y118.881 E.14654
G1 X114.847 Y110.291 E.26395
; WIPE_START
G1 F3600
M204 S6000
G1 X116.847 Y110.266 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z11.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z11.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z11.2 F4000
            G39.3 S1
            G0 Z11.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.071 Y112.538 F42000
M73 P90 R2
G1 Z10.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.186032
G1 F1200
M204 S6000
G1 X117.667 Y112.516 E.00696
M204 S10000
G1 X117.242 Y113 F42000
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.38581
G1 F1200
M204 S6000
G1 X117.242 Y113.165 E.00462
; LINE_WIDTH: 0.409515
G1 X117.266 Y113.83 E.01986
; LINE_WIDTH: 0.456925
G1 X117.29 Y114.494 E.02243
; LINE_WIDTH: 0.523778
G3 X117.313 Y116.415 I-26.898 J1.293 E.07529
G1 X117.799 Y116.415 E.01901
G1 X117.796 Y115.124 E.05058
; LINE_WIDTH: 0.504335
G1 X117.725 Y114.463 E.025
; LINE_WIDTH: 0.456925
G1 X117.654 Y113.802 E.02243
; LINE_WIDTH: 0.400425
G2 X117.562 Y112.988 I-11.449 J.893 E.02386
G1 X117.302 Y112.998 E.00756
; CHANGE_LAYER
; Z_HEIGHT: 11
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F10069.813
G1 X117.562 Y112.988 E-.18291
G1 X117.654 Y113.802 E-.57709
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 55/79
; update layer progress
M73 L55
M991 S0 P54 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z11.2 I1.102 J-.516 P1  F42000
G1 X117.019 Y112.447 Z11.2
G1 Z11
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X117.863 Y112.447 E.02798
G1 X118.245 Y115.109 E.08922
G1 X118.245 Y116.591 E.04916
G1 X118.184 Y116.776 E.00646
G1 X117.019 Y116.776 E.03862
G1 X117.019 Y112.507 E.14162
M204 S10000
G1 X116.612 Y112.04 F42000
G1 F1200
M204 S6000
G1 X118.216 Y112.04 E.05318
G1 X118.652 Y115.08 E.10189
G1 X118.652 Y116.657 E.0523
G1 X118.478 Y117.183 E.01839
G1 X116.612 Y117.183 E.06189
G1 X116.612 Y112.1 E.16863
M204 S10000
G1 X116.205 Y111.633 F42000
G1 F1200
M204 S6000
G1 X118.568 Y111.633 E.07839
G1 X119.059 Y115.051 E.11456
G1 X119.059 Y116.722 E.05543
G1 X118.772 Y117.59 E.03032
G1 X116.205 Y117.59 E.08515
G1 X116.205 Y111.693 E.19563
M204 S10000
G1 X115.798 Y111.226 F42000
G1 F1200
M204 S6000
G1 X118.921 Y111.226 E.1036
G1 X119.466 Y115.022 E.12723
G1 X119.466 Y116.788 E.05857
G1 X119.066 Y117.997 E.04225
G1 X115.798 Y117.997 E.10842
G1 X115.798 Y111.286 E.22264
M204 S10000
G1 X115.391 Y110.818 F42000
G1 F1200
M204 S6000
G1 X119.274 Y110.818 E.12881
G1 X119.873 Y114.993 E.13989
G1 X119.873 Y116.853 E.06171
G1 X119.361 Y118.404 E.05419
G1 X115.391 Y118.404 E.13168
G1 X115.391 Y110.878 E.24965
M204 S250
G1 X114.999 Y110.426 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.614 Y110.426 E.14181
G1 X120.265 Y114.965 E.14089
G1 X120.265 Y116.916 E.05995
G1 X119.644 Y118.796 E.06084
G1 X114.999 Y118.796 E.14273
G1 X114.999 Y110.486 E.25534
; WIPE_START
G1 F3600
M204 S6000
G1 X116.999 Y110.46 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z11.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z11.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z11.4 F4000
            G39.3 S1
            G0 Z11.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.471 Y112.899 F42000
G1 Z11
G1 E.8 F1800
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.56248
G1 F1200
M204 S6000
G1 X117.492 Y113.192 E.01246
; LINE_WIDTH: 0.60864
G1 X117.513 Y113.486 E.01356
M204 S10000
G1 X117.517 Y113.545 F42000
; LINE_WIDTH: 0.60956
G1 F1200
M204 S6000
G1 X117.495 Y113.612 E.00324
; LINE_WIDTH: 0.565238
G1 X117.473 Y113.678 E.00298
; LINE_WIDTH: 0.520916
G1 X117.451 Y113.745 E.00273
; LINE_WIDTH: 0.476595
G1 X117.429 Y113.811 E.00248
; LINE_WIDTH: 0.432273
G1 X117.406 Y113.878 E.00222
; LINE_WIDTH: 0.407767
G1 X117.384 Y113.944 E.00208
G1 X117.427 Y115.153 E.03595
; LINE_WIDTH: 0.45204
G1 X117.427 Y116.368 E.04051
G1 X117.837 Y116.368 E.01364
G1 X117.834 Y115.124 E.04148
; LINE_WIDTH: 0.430478
G1 X117.77 Y114.523 E.0191
; LINE_WIDTH: 0.387353
G1 X117.706 Y113.921 E.01697
; LINE_WIDTH: 0.387951
G1 X117.679 Y113.868 E.00169
; LINE_WIDTH: 0.432273
G1 X117.652 Y113.814 E.00191
; LINE_WIDTH: 0.476595
G1 X117.625 Y113.76 E.00212
; LINE_WIDTH: 0.520916
G1 X117.598 Y113.707 E.00234
; LINE_WIDTH: 0.565238
G1 X117.571 Y113.653 E.00256
; LINE_WIDTH: 0.60956
G1 X117.544 Y113.599 E.00277
; CHANGE_LAYER
; Z_HEIGHT: 11.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F6353.249
G1 X117.571 Y113.653 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 56/79
; update layer progress
M73 L56
M991 S0 P55 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z11.4 I1.132 J-.448 P1  F42000
G1 X117.171 Y112.642 Z11.4
G1 Z11.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X117.891 Y112.642 E.02386
G1 X118.245 Y115.109 E.08268
G1 X118.245 Y116.691 E.05248
G1 X117.171 Y116.691 E.0356
G1 X117.171 Y112.702 E.13233
M204 S10000
G1 X116.764 Y112.235 F42000
G1 F1200
M204 S6000
G1 X118.244 Y112.235 E.04907
G1 X118.652 Y115.08 E.09535
G1 X118.652 Y116.657 E.0523
G1 X118.506 Y117.098 E.01543
G1 X116.764 Y117.098 E.05777
G1 X116.764 Y112.295 E.15934
M204 S10000
G1 X116.357 Y111.828 F42000
G1 F1200
M204 S6000
G1 X118.596 Y111.828 E.07428
G1 X119.059 Y115.051 E.10802
G1 X119.059 Y116.722 E.05543
G1 X118.8 Y117.505 E.02736
G1 X116.357 Y117.505 E.08104
G1 X116.357 Y111.888 E.18635
M204 S10000
G1 X115.95 Y111.421 F42000
G1 F1200
M204 S6000
M73 P91 R2
G1 X118.949 Y111.421 E.09949
G1 X119.466 Y115.022 E.12068
G1 X119.466 Y116.788 E.05857
G1 X119.094 Y117.912 E.03929
G1 X115.95 Y117.912 E.1043
G1 X115.95 Y111.481 E.21335
M204 S10000
G1 X115.543 Y111.014 F42000
G1 F1200
M204 S6000
G1 X119.302 Y111.014 E.12469
G1 X119.873 Y114.993 E.13335
G1 X119.873 Y116.853 E.06171
G1 X119.389 Y118.32 E.05123
G1 X115.543 Y118.32 E.12757
G1 X115.543 Y111.074 E.24036
M204 S250
G1 X115.151 Y110.622 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.642 Y110.622 E.138
G1 X120.265 Y114.965 E.13483
G1 X120.265 Y116.916 E.05995
G1 X119.672 Y118.712 E.0581
G1 X115.151 Y118.712 E.13892
G1 X115.151 Y110.682 E.24674
; WIPE_START
G1 F3600
M204 S6000
G1 X117.151 Y110.655 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z11.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z11.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z11.6 F4000
            G39.3 S1
            G0 Z11.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.544 Y112.846 F42000
G1 Z11.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.426652
G1 F1200
M204 S6000
G1 X117.57 Y113.22 E.01174
; LINE_WIDTH: 0.466872
G1 X117.597 Y113.594 E.01297
; LINE_WIDTH: 0.507091
G1 X117.624 Y113.969 E.0142
; LINE_WIDTH: 0.547311
G1 X117.651 Y114.343 E.01543
; LINE_WIDTH: 0.587531
G1 X117.677 Y114.718 E.01666
M204 S10000
G1 X117.541 Y115.099 F42000
; FEATURE: Internal solid infill
; LINE_WIDTH: 0.376045
G1 F1200
M204 S6000
G1 X117.541 Y116.321 E.03319
G1 X117.875 Y116.321 E.00904
G1 X117.866 Y115.075 E.03382
G1 X117.601 Y115.094 E.0072
; CHANGE_LAYER
; Z_HEIGHT: 11.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F10806.754
G1 X117.866 Y115.075 E-.10082
G1 X117.875 Y116.321 E-.47338
G1 X117.541 Y116.321 E-.12659
G1 X117.541 Y116.165 E-.05921
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 57/79
; update layer progress
M73 L57
M991 S0 P56 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z11.6 I1.214 J-.08 P1  F42000
G1 X117.323 Y112.837 Z11.6
G1 Z11.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X117.919 Y112.837 E.01975
G1 X118.245 Y115.109 E.07614
G1 X118.245 Y116.606 E.04967
G1 X117.323 Y116.606 E.03056
G1 X117.323 Y112.897 E.12304
M204 S10000
G1 X116.916 Y112.43 F42000
G1 F1200
M204 S6000
G1 X118.272 Y112.43 E.04496
G1 X118.652 Y115.08 E.08881
G1 X118.652 Y116.657 E.0523
G1 X118.534 Y117.014 E.01246
G1 X116.916 Y117.014 E.05366
G1 X116.916 Y112.49 E.15005
M204 S10000
G1 X116.509 Y112.023 F42000
G1 F1200
M204 S6000
G1 X118.624 Y112.023 E.07017
G1 X119.059 Y115.051 E.10148
G1 X119.059 Y116.722 E.05543
G1 X118.828 Y117.421 E.0244
G1 X116.509 Y117.421 E.07693
G1 X116.509 Y112.083 E.17706
M204 S10000
G1 X116.102 Y111.616 F42000
G1 F1200
M204 S6000
G1 X118.977 Y111.616 E.09537
G1 X119.466 Y115.022 E.11414
G1 X119.466 Y116.788 E.05857
G1 X119.122 Y117.828 E.03633
G1 X116.102 Y117.828 E.10019
G1 X116.102 Y111.676 E.20406
M204 S10000
G1 X115.695 Y111.209 F42000
G1 F1200
M204 S6000
G1 X119.33 Y111.209 E.12058
G1 X119.873 Y114.993 E.12681
G1 X119.873 Y116.853 E.06171
G1 X119.417 Y118.235 E.04826
G1 X115.695 Y118.235 E.12346
G1 X115.695 Y111.269 E.23107
M204 S250
G1 X115.303 Y110.817 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.67 Y110.817 E.13419
G1 X120.265 Y114.965 E.12877
G1 X120.265 Y116.916 E.05995
G1 X119.7 Y118.627 E.05535
G1 X115.303 Y118.627 E.13511
G1 X115.303 Y110.877 E.23814
; WIPE_START
G1 F3600
M204 S6000
G1 X117.303 Y110.849 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z11.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z11.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z11.8 F4000
            G39.3 S1
            G0 Z11.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.634 Y113.041 F42000
G1 Z11.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.297326
G1 F1200
M204 S6000
G1 X117.659 Y113.391 E.00728
; LINE_WIDTH: 0.344568
G1 X117.684 Y113.741 E.00863
; LINE_WIDTH: 0.391811
G1 X117.709 Y114.091 E.00998
; LINE_WIDTH: 0.439054
G1 X117.734 Y114.442 E.01133
; LINE_WIDTH: 0.486296
G1 X117.759 Y114.792 E.01269
; LINE_WIDTH: 0.533539
G1 X117.784 Y115.142 E.01404
; LINE_WIDTH: 0.55716
G1 X117.784 Y116.403 E.05283
; CHANGE_LAYER
; Z_HEIGHT: 11.6
; LAYER_HEIGHT: 0.200001
; WIPE_START
G1 F7000.623
G1 X117.784 Y115.142 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 58/79
; update layer progress
M73 L58
M991 S0 P57 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z11.8 I1.204 J-.176 P1  F42000
G1 X117.475 Y113.032 Z11.8
G1 Z11.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X117.947 Y113.032 E.01564
G1 X118.245 Y115.109 E.0696
G1 X118.245 Y116.522 E.04685
G1 X117.475 Y116.522 E.02552
G1 X117.475 Y113.092 E.11376
M204 S10000
G1 X117.068 Y112.625 F42000
G1 F1200
M204 S6000
G1 X118.3 Y112.625 E.04084
G1 X118.652 Y115.08 E.08227
G1 X118.652 Y116.657 E.0523
G1 X118.562 Y116.929 E.0095
G1 X117.068 Y116.929 E.04955
G1 X117.068 Y112.685 E.14076
M204 S10000
G1 X116.661 Y112.218 F42000
G1 F1200
M204 S6000
G1 X118.652 Y112.218 E.06605
G1 X119.059 Y115.051 E.09493
G1 X119.059 Y116.722 E.05543
G1 X118.856 Y117.336 E.02143
G1 X116.661 Y117.336 E.07281
G1 X116.661 Y112.278 E.16777
M204 S10000
G1 X116.254 Y111.811 F42000
G1 F1200
M204 S6000
G1 X119.005 Y111.811 E.09126
G1 X119.466 Y115.022 E.1076
G1 X119.466 Y116.788 E.05857
G1 X119.15 Y117.743 E.03337
G1 X116.254 Y117.743 E.09608
G1 X116.254 Y111.871 E.19478
M204 S10000
G1 X115.847 Y111.404 F42000
G1 F1200
M204 S6000
G1 X119.358 Y111.404 E.11647
G1 X119.873 Y114.993 E.12027
G1 X119.873 Y116.853 E.06171
G1 X119.445 Y118.15 E.0453
G1 X115.847 Y118.15 E.11934
G1 X115.847 Y111.464 E.22178
M204 S250
G1 X115.455 Y111.012 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
M73 P91 R1
G1 X119.698 Y111.012 E.13037
M73 P92 R1
G1 X120.265 Y114.965 E.12271
G1 X120.265 Y116.916 E.05995
G1 X119.728 Y118.542 E.05261
G1 X115.455 Y118.542 E.1313
G1 X115.455 Y111.072 E.22953
; WIPE_START
G1 F3600
M204 S6000
G1 X117.455 Y111.044 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z12 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z12
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z12 F4000
            G39.3 S1
            G0 Z12 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.724 Y113.236 F42000
G1 Z11.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.162874
G1 F1200
M204 S6000
G1 X117.747 Y113.553 E.0031
; LINE_WIDTH: 0.206926
G1 X117.77 Y113.87 E.00424
; LINE_WIDTH: 0.250978
G1 X117.792 Y114.186 E.00538
; LINE_WIDTH: 0.29503
G1 X117.815 Y114.503 E.00653
; LINE_WIDTH: 0.339082
G1 X117.837 Y114.82 E.00766
; LINE_WIDTH: 0.383134
G1 X117.86 Y115.137 E.00881
; LINE_WIDTH: 0.40516
G1 X117.86 Y116.318 E.03487
; CHANGE_LAYER
; Z_HEIGHT: 11.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9938.163
G1 X117.86 Y115.137 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 59/79
; update layer progress
M73 L59
M991 S0 P58 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z12 I1.208 J-.147 P1  F42000
G1 X117.627 Y113.228 Z12
G1 Z11.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X117.975 Y113.228 E.01152
G1 X118.245 Y115.109 E.06306
G1 X118.245 Y116.437 E.04404
G1 X117.627 Y116.437 E.02048
G1 X117.627 Y113.288 E.10447
M204 S10000
G1 X117.22 Y112.82 F42000
G1 F1200
M204 S6000
G1 X118.328 Y112.82 E.03673
G1 X118.652 Y115.08 E.07573
G1 X118.652 Y116.657 E.0523
G1 X118.59 Y116.844 E.00654
G1 X117.22 Y116.844 E.04543
G1 X117.22 Y112.88 E.13147
M204 S10000
G1 X116.813 Y112.413 F42000
G1 F1200
M204 S6000
G1 X118.68 Y112.413 E.06194
G1 X119.059 Y115.051 E.08839
G1 X119.059 Y116.722 E.05543
G1 X118.884 Y117.251 E.01847
G1 X116.813 Y117.251 E.0687
G1 X116.813 Y112.473 E.15848
M204 S10000
G1 X116.406 Y112.006 F42000
G1 F1200
M204 S6000
G1 X119.033 Y112.006 E.08715
G1 X119.466 Y115.022 E.10106
G1 X119.466 Y116.788 E.05857
G1 X119.178 Y117.658 E.03041
G1 X116.406 Y117.658 E.09196
G1 X116.406 Y112.066 E.18549
M204 S10000
G1 X115.999 Y111.599 F42000
G1 F1200
M204 S6000
G1 X119.386 Y111.599 E.11235
G1 X119.873 Y114.993 E.11373
G1 X119.873 Y116.853 E.06171
G1 X119.473 Y118.065 E.04234
G1 X115.999 Y118.065 E.11523
G1 X115.999 Y111.659 E.21249
M204 S250
G1 X115.607 Y111.207 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.726 Y111.207 E.12656
G1 X120.265 Y114.965 E.11665
G1 X120.265 Y116.916 E.05995
G1 X119.756 Y118.457 E.04987
G1 X115.607 Y118.457 E.12749
G1 X115.607 Y111.267 E.22093
; WIPE_START
G1 F3600
M204 S6000
G1 X117.607 Y111.238 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z12.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z12.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z12.2 F4000
            G39.3 S1
            G0 Z12.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X117.856 Y114.01 F42000
G1 Z11.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.116456
G1 F1200
M204 S6000
G1 X117.876 Y114.29 E.00168
; LINE_WIDTH: 0.155515
G1 X117.896 Y114.57 E.00258
; LINE_WIDTH: 0.194573
G1 X117.916 Y114.851 E.00347
; LINE_WIDTH: 0.233631
G1 X117.936 Y115.131 E.00437
; LINE_WIDTH: 0.25316
G1 X117.936 Y116.233 E.01888
; CHANGE_LAYER
; Z_HEIGHT: 12
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F15000
G1 X117.936 Y115.131 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 60/79
; update layer progress
M73 L60
M991 S0 P59 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z12.2 I1.212 J-.114 P1  F42000
G1 X117.779 Y113.463 Z12.2
G1 Z12
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.006 Y113.447 E.00754
G1 X118.245 Y115.109 E.05571
G1 X118.245 Y116.352 E.04123
G1 X117.779 Y116.352 E.01544
G1 X117.779 Y113.523 E.09385
M204 S10000
G1 X117.372 Y113.016 F42000
G1 F1200
M204 S6000
G1 X118.356 Y113.016 E.03262
G1 X118.652 Y115.08 E.06918
G1 X118.652 Y116.759 E.05569
G1 X117.372 Y116.759 E.04244
G1 X117.372 Y113.076 E.12219
M204 S10000
G1 X116.965 Y112.609 F42000
G1 F1200
M204 S6000
G1 X118.708 Y112.609 E.05783
G1 X119.059 Y115.051 E.08185
G1 X119.059 Y116.722 E.05543
G1 X118.912 Y117.166 E.01551
G1 X116.965 Y117.166 E.06459
G1 X116.965 Y112.669 E.14919
M204 S10000
G1 X116.558 Y112.202 F42000
G1 F1200
M204 S6000
G1 X119.061 Y112.202 E.08303
G1 X119.466 Y115.022 E.09452
G1 X119.466 Y116.788 E.05857
G1 X119.206 Y117.573 E.02744
G1 X116.558 Y117.573 E.08785
G1 X116.558 Y112.262 E.1762
M204 S10000
G1 X116.151 Y111.794 F42000
G1 F1200
M204 S6000
G1 X119.414 Y111.794 E.10824
G1 X119.873 Y114.993 E.10719
G1 X119.873 Y116.853 E.06171
G1 X119.501 Y117.98 E.03938
G1 X116.151 Y117.98 E.11112
G1 X116.151 Y111.854 E.20321
M204 S250
G1 X115.759 Y111.402 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.754 Y111.402 E.12275
G1 X120.265 Y114.965 E.11059
G1 X120.265 Y116.916 E.05995
G1 X119.784 Y118.372 E.04712
G1 X115.759 Y118.372 E.12368
G1 X115.759 Y111.462 E.21233
; WIPE_START
G1 F3600
M204 S6000
G1 X117.759 Y111.432 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z12.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z12.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z12.4 F4000
            G39.3 S1
            G0 Z12.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X118.008 Y115.069 F42000
G1 Z12
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.101049
G1 F1200
M204 S6000
G1 X118.012 Y116.149 E.00511
; CHANGE_LAYER
; Z_HEIGHT: 12.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F15000
G1 X118.008 Y115.069 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 61/79
; update layer progress
M73 L61
M991 S0 P60 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z12.4 I1.205 J-.169 P1  F42000
G1 X117.931 Y114.523 Z12.4
G1 Z12.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.158 Y114.506 E.00754
M73 P93 R1
G1 X118.245 Y115.109 E.0202
G1 X118.245 Y116.267 E.03841
G1 X117.931 Y116.267 E.01039
G1 X117.931 Y114.583 E.05588
; WIPE_START
G1 F8843.478
G1 X118.158 Y114.506 E-.09093
G1 X118.245 Y115.109 E-.23142
G1 X118.245 Y116.261 E-.43765
; WIPE_END
G1 E-.04 F1800
M204 S10000
G1 X117.524 Y113.211 Z12.6 F42000
G1 Z12.2
G1 E.8 F1800
G1 F1200
M204 S6000
G1 X118.384 Y113.211 E.0285
G1 X118.652 Y115.08 E.06264
G1 X118.652 Y116.674 E.05288
G1 X117.524 Y116.674 E.0374
G1 X117.524 Y113.271 E.1129
M204 S10000
G1 X117.117 Y112.804 F42000
G1 F1200
M204 S6000
G1 X118.736 Y112.804 E.05371
G1 X119.059 Y115.051 E.07531
G1 X119.059 Y116.722 E.05543
G1 X118.94 Y117.081 E.01255
G1 X117.117 Y117.081 E.06047
G1 X117.117 Y112.864 E.13991
M204 S10000
G1 X116.71 Y112.397 F42000
G1 F1200
M204 S6000
G1 X119.089 Y112.397 E.07892
G1 X119.466 Y115.022 E.08798
G1 X119.466 Y116.788 E.05857
G1 X119.234 Y117.488 E.02448
G1 X116.71 Y117.488 E.08374
G1 X116.71 Y112.457 E.16691
M204 S10000
G1 X116.303 Y111.99 F42000
G1 F1200
M204 S6000
G1 X119.442 Y111.99 E.10413
G1 X119.873 Y114.993 E.10065
G1 X119.873 Y116.853 E.06171
G1 X119.529 Y117.896 E.03641
G1 X116.303 Y117.896 E.107
G1 X116.303 Y112.05 E.19392
M204 S250
G1 X115.911 Y111.598 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.782 Y111.598 E.11894
G1 X120.265 Y114.965 E.10453
G1 X120.265 Y116.916 E.05995
G1 X119.812 Y118.288 E.04438
G1 X115.911 Y118.288 E.11987
G1 X115.911 Y111.658 E.20372
; WIPE_START
G1 F3600
M204 S6000
G1 X117.911 Y111.627 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z12.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z12.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z12.6 F4000
            G39.3 S1
            G0 Z12.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




; CHANGE_LAYER
; Z_HEIGHT: 12.4
; LAYER_HEIGHT: 0.2
; layer num/total_layer_count: 62/79
; update layer progress
M73 L62
M991 S0 P61 ;notify layer change
; OBJECT_ID: 105
G1 X117.676 Y113.406 F42000
G1 Z12.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.412 Y113.406 E.02439
G1 X118.652 Y115.08 E.0561
G1 X118.652 Y116.59 E.05007
G1 X117.676 Y116.59 E.03236
G1 X117.676 Y113.466 E.10361
M204 S10000
G1 X117.269 Y112.999 F42000
G1 F1200
M204 S6000
G1 X118.764 Y112.999 E.0496
G1 X119.059 Y115.051 E.06877
G1 X119.059 Y116.722 E.05543
G1 X118.968 Y116.997 E.00958
G1 X117.269 Y116.997 E.05636
G1 X117.269 Y113.059 E.13062
M204 S10000
G1 X116.862 Y112.592 F42000
G1 F1200
M204 S6000
G1 X119.117 Y112.592 E.07481
G1 X119.466 Y115.022 E.08144
G1 X119.466 Y116.788 E.05857
G1 X119.262 Y117.404 E.02152
G1 X116.862 Y117.404 E.07962
G1 X116.862 Y112.652 E.15762
M204 S10000
G1 X116.455 Y112.185 F42000
G1 F1200
M204 S6000
G1 X119.47 Y112.185 E.10002
G1 X119.873 Y114.993 E.0941
G1 X119.873 Y116.853 E.06171
G1 X119.557 Y117.811 E.03345
G1 X116.455 Y117.811 E.10289
G1 X116.455 Y112.245 E.18463
M204 S250
G1 X116.063 Y111.793 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.81 Y111.793 E.11513
G1 X120.265 Y114.965 E.09847
G1 X120.265 Y116.916 E.05995
G1 X119.84 Y118.203 E.04163
G1 X116.063 Y118.203 E.11606
G1 X116.063 Y111.853 E.19512
; WIPE_START
G1 F3600
M204 S6000
G1 X118.063 Y111.821 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z12.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z12.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z12.8 F4000
            G39.3 S1
            G0 Z12.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X118.057 Y113.61 F42000
G1 Z12.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.447075
G1 F1200
M204 S6000
G1 X118.083 Y113.986 E.01243
; LINE_WIDTH: 0.493997
G1 X118.11 Y114.362 E.01387
; LINE_WIDTH: 0.540918
G1 X118.137 Y114.739 E.01531
; LINE_WIDTH: 0.58784
G1 X118.164 Y115.115 E.01675
; LINE_WIDTH: 0.6113
G1 X118.164 Y116.386 E.05887
; CHANGE_LAYER
; Z_HEIGHT: 12.6
; LAYER_HEIGHT: 0.200001
; WIPE_START
G1 F6333.791
G1 X118.164 Y115.115 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 63/79
; update layer progress
M73 L63
M991 S0 P62 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z12.8 I1.188 J-.264 P1  F42000
G1 X117.828 Y113.601 Z12.8
G1 Z12.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.44 Y113.601 E.02028
G1 X118.652 Y115.08 E.04956
G1 X118.652 Y116.505 E.04726
G1 X117.828 Y116.505 E.02732
G1 X117.828 Y113.661 E.09432
M204 S10000
G1 X117.421 Y113.194 F42000
G1 F1200
M204 S6000
G1 X118.792 Y113.194 E.04549
G1 X119.059 Y115.051 E.06223
G1 X119.059 Y116.722 E.05543
G1 X118.996 Y116.912 E.00662
G1 X117.421 Y116.912 E.05225
G1 X117.421 Y113.254 E.12133
M204 S10000
G1 X117.014 Y112.787 F42000
G1 F1200
M204 S6000
G1 X119.145 Y112.787 E.07069
G1 X119.466 Y115.022 E.07489
G1 X119.466 Y116.788 E.05857
G1 X119.29 Y117.319 E.01856
G1 X117.014 Y117.319 E.07551
G1 X117.014 Y112.847 E.14834
M204 S10000
G1 X116.607 Y112.38 F42000
G1 F1200
M204 S6000
G1 X119.498 Y112.38 E.0959
G1 X119.873 Y114.993 E.08756
G1 X119.873 Y116.853 E.06171
G1 X119.585 Y117.726 E.03049
G1 X116.607 Y117.726 E.09878
G1 X116.607 Y112.44 E.17534
M204 S250
G1 X116.215 Y111.988 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.838 Y111.988 E.11132
G1 X120.265 Y114.965 E.09241
G1 X120.265 Y116.916 E.05995
G1 X119.868 Y118.118 E.03889
G1 X116.215 Y118.118 E.11225
G1 X116.215 Y112.048 E.18651
; WIPE_START
G1 F3600
M204 S6000
G1 X118.215 Y112.015 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z13 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z13
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z13 F4000
            G39.3 S1
            G0 Z13 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X118.147 Y113.805 F42000
G1 Z12.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.311826
G1 F1200
M204 S6000
G1 X118.17 Y114.131 E.00717
; LINE_WIDTH: 0.353961
G1 X118.193 Y114.457 E.00829
; LINE_WIDTH: 0.396097
G1 X118.217 Y114.783 E.00941
; LINE_WIDTH: 0.438233
G1 X118.24 Y115.11 E.01053
; LINE_WIDTH: 0.4593
G1 X118.24 Y116.301 E.04043
; CHANGE_LAYER
; Z_HEIGHT: 12.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F8645.948
G1 X118.24 Y115.11 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 64/79
; update layer progress
M73 L64
M991 S0 P63 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
M73 P94 R1
G3 Z13 I1.194 J-.236 P1  F42000
G1 X117.98 Y113.796 Z13
G1 Z12.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.468 Y113.796 E.01616
G1 X118.652 Y115.08 E.04302
G1 X118.652 Y116.42 E.04444
G1 X117.98 Y116.42 E.02227
G1 X117.98 Y113.856 E.08503
M204 S10000
G1 X117.573 Y113.389 F42000
G1 F1200
M204 S6000
G1 X118.82 Y113.389 E.04137
G1 X119.059 Y115.051 E.05569
G1 X119.059 Y116.722 E.05544
G1 X119.024 Y116.827 E.00366
G1 X117.573 Y116.827 E.04813
G1 X117.573 Y113.449 E.11204
M204 S10000
G1 X117.166 Y112.982 F42000
G1 F1200
M204 S6000
G1 X119.173 Y112.982 E.06658
G1 X119.466 Y115.022 E.06835
G1 X119.466 Y116.788 E.05857
G1 X119.318 Y117.234 E.01559
G1 X117.166 Y117.234 E.0714
G1 X117.166 Y113.042 E.13905
M204 S10000
G1 X116.759 Y112.575 F42000
G1 F1200
M204 S6000
G1 X119.526 Y112.575 E.09179
G1 X119.873 Y114.993 E.08102
G1 X119.873 Y116.853 E.06171
G1 X119.613 Y117.641 E.02753
G1 X116.759 Y117.641 E.09466
G1 X116.759 Y112.635 E.16605
M204 S250
G1 X116.367 Y112.183 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.866 Y112.183 E.10751
G1 X120.265 Y114.965 E.08635
G1 X120.265 Y116.916 E.05995
G1 X119.896 Y118.033 E.03615
G1 X116.367 Y118.033 E.10844
G1 X116.367 Y112.243 E.17791
; WIPE_START
G1 F3600
M204 S6000
G1 X118.367 Y112.209 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z13.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z13.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z13.2 F4000
            G39.3 S1
            G0 Z13.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X118.237 Y114 F42000
G1 Z12.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.182815
G1 F1200
M204 S6000
G1 X118.263 Y114.368 E.00421
; LINE_WIDTH: 0.232609
G1 X118.29 Y114.736 E.0057
; LINE_WIDTH: 0.282403
G1 X118.316 Y115.104 E.0072
; LINE_WIDTH: 0.3073
G1 X118.316 Y116.216 E.02396
; CHANGE_LAYER
; Z_HEIGHT: 13
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F13616.762
G1 X118.316 Y115.104 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 65/79
; update layer progress
M73 L65
M991 S0 P64 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z13.2 I1.201 J-.198 P1  F42000
G1 X118.132 Y113.992 Z13.2
G1 Z13
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.496 Y113.992 E.01205
G1 X118.652 Y115.08 E.03648
G1 X118.652 Y116.335 E.04163
G1 X118.132 Y116.335 E.01723
G1 X118.132 Y114.052 E.07575
M204 S10000
G1 X117.725 Y113.585 F42000
G1 F1200
M204 S6000
G1 X118.848 Y113.585 E.03726
G1 X119.059 Y115.051 E.04914
G1 X119.059 Y116.742 E.0561
G1 X117.725 Y116.742 E.04424
G1 X117.725 Y113.645 E.10275
M204 S10000
G1 X117.318 Y113.178 F42000
G1 F1200
M204 S6000
G1 X119.201 Y113.178 E.06247
G1 X119.466 Y115.022 E.06181
G1 X119.466 Y116.788 E.05857
G1 X119.346 Y117.149 E.01263
G1 X117.318 Y117.149 E.06728
G1 X117.318 Y113.238 E.12976
M204 S10000
G1 X116.911 Y112.77 F42000
G1 F1200
M204 S6000
G1 X119.554 Y112.77 E.08768
G1 X119.873 Y114.993 E.07448
G1 X119.873 Y116.853 E.06171
G1 X119.641 Y117.556 E.02456
G1 X116.911 Y117.556 E.09055
G1 X116.911 Y112.83 E.15677
M204 S250
G1 X116.519 Y112.378 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.894 Y112.378 E.1037
G1 X120.265 Y114.965 E.08029
G1 X120.265 Y116.916 E.05995
G1 X119.924 Y117.948 E.0334
G1 X116.519 Y117.948 E.10463
G1 X116.519 Y112.438 E.16931
; WIPE_START
G1 F3600
M204 S6000
G1 X118.519 Y112.403 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z13.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z13.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z13.4 F4000
            G39.3 S1
            G0 Z13.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X118.361 Y114.663 F42000
G1 Z13
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.11152
G1 F1200
M204 S6000
G1 X118.376 Y114.881 E.00122
; LINE_WIDTH: 0.140707
G1 X118.392 Y115.099 E.00174
; LINE_WIDTH: 0.1553
G1 X118.392 Y116.132 E.00946
; CHANGE_LAYER
; Z_HEIGHT: 13.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F15000
G1 X118.392 Y115.099 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 66/79
; update layer progress
M73 L66
M991 S0 P65 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z13.4 I1.209 J-.143 P1  F42000
G1 X118.284 Y114.187 Z13.4
G1 Z13.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.524 Y114.187 E.00794
G1 X118.652 Y115.08 E.02994
G1 X118.652 Y116.25 E.03882
G1 X118.284 Y116.25 E.01219
G1 X118.284 Y114.247 E.06646
M204 S10000
G1 X117.877 Y113.78 F42000
G1 F1200
M204 S6000
G1 X118.876 Y113.78 E.03315
G1 X119.059 Y115.051 E.0426
G1 X119.059 Y116.657 E.05328
G1 X117.877 Y116.657 E.0392
G1 X117.877 Y113.84 E.09346
M204 S10000
G1 X117.47 Y113.373 F42000
G1 F1200
M204 S6000
G1 X119.229 Y113.373 E.05835
G1 X119.466 Y115.022 E.05527
G1 X119.466 Y116.788 E.05857
G1 X119.374 Y117.064 E.00967
G1 X117.47 Y117.064 E.06317
G1 X117.47 Y113.433 E.12047
M204 S10000
G1 X117.063 Y112.966 F42000
G1 F1200
M204 S6000
G1 X119.582 Y112.966 E.08356
G1 X119.873 Y114.993 E.06794
G1 X119.873 Y116.853 E.06171
G1 X119.669 Y117.472 E.0216
G1 X117.063 Y117.472 E.08644
G1 X117.063 Y113.026 E.14748
M204 S250
G1 X116.671 Y112.574 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.922 Y112.574 E.09989
G1 X120.265 Y114.965 E.07423
G1 X120.265 Y116.916 E.05995
M73 P95 R1
G1 X119.952 Y117.864 E.03066
G1 X116.671 Y117.864 E.10082
G1 X116.671 Y112.634 E.1607
; WIPE_START
G1 F3600
M204 S6000
G1 X118.671 Y112.597 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z13.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z13.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z13.6 F4000
            G39.3 S1
            G0 Z13.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




; CHANGE_LAYER
; Z_HEIGHT: 13.4
; LAYER_HEIGHT: 0.2
; layer num/total_layer_count: 67/79
; update layer progress
M73 L67
M991 S0 P66 ;notify layer change
; OBJECT_ID: 105
G1 X118.029 Y113.975 F42000
G1 Z13.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.904 Y113.975 E.02903
G1 X119.059 Y115.051 E.03606
G1 X119.059 Y116.573 E.05047
G1 X118.029 Y116.573 E.03415
G1 X118.029 Y114.035 E.08418
M204 S10000
G1 X117.622 Y113.568 F42000
G1 F1200
M204 S6000
G1 X119.257 Y113.568 E.05424
G1 X119.466 Y115.022 E.04873
G1 X119.466 Y116.788 E.05857
G1 X119.402 Y116.98 E.00671
G1 X117.622 Y116.98 E.05906
G1 X117.622 Y113.628 E.11118
M204 S10000
G1 X117.215 Y113.161 F42000
G1 F1200
M204 S6000
G1 X119.61 Y113.161 E.07945
G1 X119.873 Y114.993 E.0614
G1 X119.873 Y116.853 E.06171
G1 X119.697 Y117.387 E.01864
G1 X117.215 Y117.387 E.08232
G1 X117.215 Y113.221 E.13819
M204 S250
G1 X116.823 Y112.769 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.95 Y112.769 E.09608
G1 X120.265 Y114.965 E.06817
G1 X120.265 Y116.916 E.05995
G1 X119.98 Y117.779 E.02791
G1 X116.823 Y117.779 E.09701
G1 X116.823 Y112.829 E.1521
; WIPE_START
G1 F3600
M204 S6000
G1 X118.823 Y112.79 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z13.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z13.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z13.8 F4000
            G39.3 S1
            G0 Z13.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X118.479 Y114.179 F42000
G1 Z13.4
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.596493
G1 F1200
M204 S6000
G1 X118.512 Y114.633 E.02056
; LINE_WIDTH: 0.642458
G1 X118.544 Y115.088 E.02227
; LINE_WIDTH: 0.66544
G1 X118.544 Y116.369 E.06499
; CHANGE_LAYER
; Z_HEIGHT: 13.6
; LAYER_HEIGHT: 0.200001
; WIPE_START
G1 F5782.947
G1 X118.544 Y115.088 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 68/79
; update layer progress
M73 L68
M991 S0 P67 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z13.8 I1.132 J-.447 P1  F42000
G1 X118.181 Y114.17 Z13.8
G1 Z13.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.932 Y114.17 E.02492
G1 X119.059 Y115.051 E.02952
G1 X119.059 Y116.488 E.04766
G1 X118.181 Y116.488 E.02911
G1 X118.181 Y114.23 E.07489
M204 S10000
G1 X117.774 Y113.763 F42000
G1 F1200
M204 S6000
G1 X119.285 Y113.763 E.05013
G1 X119.466 Y115.022 E.04219
G1 X119.466 Y116.788 E.05857
G1 X119.431 Y116.895 E.00374
G1 X117.774 Y116.895 E.05495
G1 X117.774 Y113.823 E.10189
M204 S10000
G1 X117.367 Y113.356 F42000
G1 F1200
M204 S6000
G1 X119.638 Y113.356 E.07534
G1 X119.873 Y114.993 E.05486
G1 X119.873 Y116.853 E.06171
G1 X119.725 Y117.302 E.01568
G1 X117.367 Y117.302 E.07821
G1 X117.367 Y113.416 E.1289
M204 S250
G1 X116.975 Y112.964 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X119.978 Y112.964 E.09227
G1 X120.265 Y114.965 E.06211
G1 X120.265 Y116.916 E.05995
G1 X120.008 Y117.694 E.02517
G1 X116.975 Y117.694 E.0932
G1 X116.975 Y113.024 E.1435
; WIPE_START
G1 F3600
M204 S6000
G1 X118.975 Y112.984 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z14 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z14
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z14 F4000
            G39.3 S1
            G0 Z14 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X118.569 Y114.374 F42000
G1 Z13.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.458864
G1 F1200
M204 S6000
G1 X118.595 Y114.728 E.01204
; LINE_WIDTH: 0.495248
G1 X118.62 Y115.082 E.01309
; LINE_WIDTH: 0.51344
G1 X118.62 Y116.284 E.04608
; CHANGE_LAYER
; Z_HEIGHT: 13.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F7651.109
G1 X118.62 Y115.082 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 69/79
; update layer progress
M73 L69
M991 S0 P68 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z14 I1.13 J-.452 P1  F42000
G1 X118.333 Y114.365 Z14
G1 Z13.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.96 Y114.365 E.02081
G1 X119.059 Y115.051 E.02298
G1 X119.059 Y116.403 E.04484
G1 X118.333 Y116.403 E.02407
G1 X118.333 Y114.425 E.0656
M204 S10000
G1 X117.926 Y113.958 F42000
G1 F1200
M204 S6000
G1 X119.313 Y113.958 E.04601
G1 X119.466 Y115.022 E.03565
G1 X119.466 Y116.81 E.05931
G1 X117.926 Y116.81 E.05108
G1 X117.926 Y114.018 E.09261
M204 S10000
G1 X117.519 Y113.551 F42000
G1 F1200
M204 S6000
G1 X119.666 Y113.551 E.07122
G1 X119.873 Y114.993 E.04831
G1 X119.873 Y116.853 E.06171
G1 X119.753 Y117.217 E.01272
G1 X117.519 Y117.217 E.0741
G1 X117.519 Y113.611 E.11961
M204 S250
G1 X117.127 Y113.159 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.006 Y113.159 E.08846
G1 X120.265 Y114.965 E.05606
G1 X120.265 Y116.916 E.05995
G1 X120.036 Y117.609 E.02243
G1 X117.127 Y117.609 E.08939
G1 X117.127 Y113.219 E.13489
; WIPE_START
G1 F3600
M204 S6000
G1 X119.127 Y113.178 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z14.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z14.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z14.2 F4000
            G39.3 S1
            G0 Z14.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X118.66 Y114.569 F42000
G1 Z13.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.321221
G1 F1200
M204 S6000
G1 X118.678 Y114.823 E.00578
; LINE_WIDTH: 0.348034
G1 X118.696 Y115.077 E.00633
; LINE_WIDTH: 0.36144
G1 X118.696 Y116.199 E.02913
; CHANGE_LAYER
; Z_HEIGHT: 14
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F11302.273
G1 X118.696 Y115.077 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 70/79
; update layer progress
M73 L70
M991 S0 P69 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z14.2 I1.127 J-.46 P1  F42000
G1 X118.485 Y114.561 Z14.2
G1 Z14
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X118.988 Y114.561 E.01669
G1 X119.059 Y115.051 E.01644
G1 X119.059 Y116.318 E.04203
G1 X118.485 Y116.318 E.01903
G1 X118.485 Y114.621 E.05631
M204 S10000
G1 X118.078 Y114.154 F42000
G1 F1200
M204 S6000
G1 X119.341 Y114.154 E.0419
G1 X119.466 Y115.022 E.0291
G1 X119.466 Y116.725 E.0565
G1 X118.078 Y116.725 E.04603
G1 X118.078 Y114.214 E.08332
M204 S10000
G1 X117.671 Y113.746 F42000
M73 P96 R1
G1 F1200
M204 S6000
M73 P96 R0
G1 X119.694 Y113.746 E.06711
G1 X119.873 Y114.993 E.04177
G1 X119.873 Y116.853 E.06171
G1 X119.781 Y117.132 E.00975
G1 X117.671 Y117.132 E.06998
G1 X117.671 Y113.806 E.11033
M204 S250
G1 X117.279 Y113.354 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.034 Y113.354 E.08465
G1 X120.265 Y114.965 E.05
G1 X120.265 Y116.916 E.05995
G1 X120.064 Y117.524 E.01968
G1 X117.279 Y117.524 E.08558
G1 X117.279 Y113.414 E.12629
; WIPE_START
G1 F3600
M204 S6000
G1 X119.279 Y113.371 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z14.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z14.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z14.4 F4000
            G39.3 S1
            G0 Z14.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X118.75 Y114.764 F42000
G1 Z14
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.205509
G1 F1200
M204 S6000
G1 X118.772 Y115.072 E.00408
G1 X118.772 Y116.115 E.01382
; CHANGE_LAYER
; Z_HEIGHT: 14.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F15000
G1 X118.772 Y115.072 E-.58663
G1 X118.75 Y114.764 E-.17337
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 71/79
; update layer progress
M73 L71
M991 S0 P70 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z14.4 I.09 J-1.214 P1  F42000
G1 X118.637 Y114.756 Z14.4
G1 Z14.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X119.016 Y114.756 E.01258
G1 X119.059 Y115.051 E.0099
G1 X119.059 Y116.233 E.03922
G1 X118.637 Y116.233 E.01398
G1 X118.637 Y114.816 E.04702
M204 S10000
G1 X118.23 Y114.349 F42000
G1 F1200
M204 S6000
G1 X119.369 Y114.349 E.03779
G1 X119.466 Y115.022 E.02256
G1 X119.466 Y116.64 E.05369
G1 X118.23 Y116.64 E.04099
G1 X118.23 Y114.409 E.07403
M204 S10000
G1 X117.823 Y113.942 F42000
G1 F1200
M204 S6000
G1 X119.722 Y113.942 E.063
G1 X119.873 Y114.993 E.03523
G1 X119.873 Y116.853 E.06171
G1 X119.809 Y117.048 E.00679
G1 X117.823 Y117.048 E.06587
G1 X117.823 Y114.002 E.10104
M204 S250
G1 X117.431 Y113.55 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.062 Y113.55 E.08084
G1 X120.265 Y114.965 E.04394
G1 X120.265 Y116.916 E.05995
G1 X120.092 Y117.44 E.01694
G1 X117.431 Y117.44 E.08177
G1 X117.431 Y113.61 E.11769
; WIPE_START
G1 F3600
M204 S6000
G1 X119.43 Y113.564 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z14.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z14.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z14.6 F4000
            G39.3 S1
            G0 Z14.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




; CHANGE_LAYER
; Z_HEIGHT: 14.4
; LAYER_HEIGHT: 0.2
; layer num/total_layer_count: 72/79
; update layer progress
M73 L72
M991 S0 P71 ;notify layer change
; OBJECT_ID: 105
G1 X118.789 Y114.951 F42000
G1 Z14.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X119.059 Y114.951 E.00894
G1 X119.059 Y116.149 E.03973
G1 X118.789 Y116.149 E.00894
G1 X118.789 Y115.011 E.03774
M204 S10000
G1 X118.382 Y114.544 F42000
G1 F1200
M204 S6000
G1 X119.397 Y114.544 E.03367
G1 X119.466 Y115.022 E.01602
G1 X119.466 Y116.556 E.05087
G1 X118.382 Y116.556 E.03595
G1 X118.382 Y114.604 E.06474
M204 S10000
G1 X117.975 Y114.137 F42000
G1 F1200
M204 S6000
G1 X119.75 Y114.137 E.05888
G1 X119.873 Y114.993 E.02869
G1 X119.873 Y116.853 E.06171
G1 X119.837 Y116.963 E.00383
G1 X117.975 Y116.963 E.06175
G1 X117.975 Y114.197 E.09175
M204 S250
G1 X117.583 Y113.745 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.09 Y113.745 E.07703
G1 X120.265 Y114.965 E.03788
G1 X120.265 Y116.916 E.05995
G1 X120.12 Y117.355 E.01419
G1 X117.583 Y117.355 E.07796
G1 X117.583 Y113.805 E.10908
; WIPE_START
G1 F3600
M204 S6000
G1 X119.582 Y113.757 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z14.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z14.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z14.8 F4000
            G39.3 S1
            G0 Z14.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




; CHANGE_LAYER
; Z_HEIGHT: 14.6
; LAYER_HEIGHT: 0.200001
; layer num/total_layer_count: 73/79
; update layer progress
M73 L73
M991 S0 P72 ;notify layer change
; OBJECT_ID: 105
G1 X118.534 Y114.739 F42000
G1 Z14.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X119.425 Y114.739 E.02956
G1 X119.466 Y115.022 E.00948
G1 X119.466 Y116.471 E.04806
G1 X118.534 Y116.471 E.03091
G1 X118.534 Y114.799 E.05545
M204 S10000
G1 X118.127 Y114.332 F42000
G1 F1200
M204 S6000
G1 X119.778 Y114.332 E.05477
G1 X119.873 Y114.993 E.02215
G1 X119.873 Y116.878 E.06253
G1 X118.127 Y116.878 E.05791
G1 X118.127 Y114.392 E.08246
M204 S250
G1 X117.735 Y113.94 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.118 Y113.94 E.07322
G1 X120.265 Y114.965 E.03182
G1 X120.265 Y116.916 E.05995
G1 X120.148 Y117.27 E.01145
G1 X117.735 Y117.27 E.07415
G1 X117.735 Y114 E.10048
; WIPE_START
G1 F3600
M204 S6000
G1 X119.734 Y113.95 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z15 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z15
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z15 F4000
            G39.3 S1
            G0 Z15 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X119 Y114.943 F42000
G1 Z14.6
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.56758
G1 F1200
M204 S6000
G1 X119 Y116.267 E.05663
; CHANGE_LAYER
; Z_HEIGHT: 14.8
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F6861.587
G1 X119 Y114.943 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 74/79
; update layer progress
M73 L74
M991 S0 P73 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z15 I.032 J-1.217 P1  F42000
G1 X118.686 Y114.934 Z15
G1 Z14.8
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X119.466 Y114.934 E.02587
G1 X119.466 Y116.386 E.04816
G1 X118.686 Y116.386 E.02587
G1 X118.686 Y114.994 E.04617
M204 S10000
G1 X118.279 Y114.527 F42000
G1 F1200
M204 S6000
G1 X119.806 Y114.527 E.05066
G1 X119.873 Y114.993 E.01561
G1 X119.873 Y116.793 E.05971
G1 X118.279 Y116.793 E.05287
G1 X118.279 Y114.587 E.07317
M204 S250
G1 X117.887 Y114.135 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.146 Y114.135 E.06941
G1 X120.265 Y114.965 E.02576
G1 X120.265 Y116.916 E.05995
G1 X120.176 Y117.185 E.0087
G1 X117.887 Y117.185 E.07034
G1 X117.887 Y114.195 E.09187
; WIPE_START
G1 F3600
M204 S6000
G1 X119.886 Y114.142 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z15.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z15.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z15.2 F4000
            G39.3 S1
            G0 Z15.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X119.076 Y115.138 F42000
G1 Z14.8
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.41558
G1 F1200
M204 S6000
M73 P97 R0
G1 X119.076 Y116.183 E.03172
; CHANGE_LAYER
; Z_HEIGHT: 15
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F9660.28
G1 X119.076 Y115.138 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 75/79
; update layer progress
M73 L75
M991 S0 P74 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z15.2 I.043 J-1.216 P1  F42000
G1 X118.838 Y115.13 Z15.2
G1 Z15
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X119.466 Y115.13 E.02082
G1 X119.466 Y116.301 E.03887
G1 X118.838 Y116.301 E.02082
G1 X118.838 Y115.19 E.03688
M204 S10000
G1 X118.431 Y114.722 F42000
G1 F1200
M204 S6000
G1 X119.834 Y114.722 E.04654
G1 X119.873 Y114.993 E.00907
G1 X119.873 Y116.708 E.0569
G1 X118.431 Y116.708 E.04783
G1 X118.431 Y114.782 E.06388
M204 S250
G1 X118.039 Y114.33 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.174 Y114.33 E.0656
G1 X120.265 Y114.965 E.0197
G1 X120.265 Y116.916 E.05995
G1 X120.204 Y117.1 E.00596
G1 X118.039 Y117.1 E.06653
G1 X118.039 Y114.39 E.08327
; WIPE_START
G1 F3600
M204 S6000
G1 X120.038 Y114.334 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z15.4 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z15.4
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z15.4 F4000
            G39.3 S1
            G0 Z15.4 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X119.152 Y115.333 F42000
G1 Z15
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.26358
G1 F1200
M204 S6000
G1 X119.152 Y116.098 E.01375
; CHANGE_LAYER
; Z_HEIGHT: 15.2
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F15000
G1 X119.152 Y115.333 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 76/79
; update layer progress
M73 L76
M991 S0 P75 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z15.4 I.063 J-1.215 P1  F42000
G1 X118.99 Y115.325 Z15.4
G1 Z15.2
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X119.466 Y115.325 E.01578
G1 X119.466 Y116.216 E.02958
G1 X118.99 Y116.216 E.01578
G1 X118.99 Y115.385 E.02759
M204 S10000
G1 X118.583 Y114.918 F42000
G1 F1200
M204 S6000
G1 X119.873 Y114.918 E.04279
G1 X119.873 Y116.624 E.05659
G1 X118.583 Y116.624 E.04279
G1 X118.583 Y114.978 E.0546
M204 S250
G1 X118.191 Y114.526 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.202 Y114.526 E.06179
G1 X120.265 Y114.965 E.01364
G1 X120.265 Y116.916 E.05995
G1 X120.232 Y117.016 E.00322
G1 X118.191 Y117.016 E.06272
G1 X118.191 Y114.586 E.07467
; WIPE_START
G1 F3600
M204 S6000
G1 X120.19 Y114.526 E-.76
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z15.6 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z15.6
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z15.6 F4000
            G39.3 S1
            G0 Z15.6 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X119.228 Y115.528 F42000
G1 Z15.2
G1 E.8 F1800
; FEATURE: Gap infill
; LINE_WIDTH: 0.11158
G1 F1200
M204 S6000
G1 X119.228 Y116.013 E.00271
; CHANGE_LAYER
; Z_HEIGHT: 15.4
; LAYER_HEIGHT: 0.2
; WIPE_START
G1 F15000
G1 X119.228 Y115.528 E-.76
; WIPE_END
G1 E-.04 F1800
; layer num/total_layer_count: 77/79
; update layer progress
M73 L77
M991 S0 P76 ;notify layer change
; OBJECT_ID: 105
M204 S10000
G17
G3 Z15.6 I.118 J-1.211 P1  F42000
G1 X119.142 Y115.52 Z15.6
G1 Z15.4
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X119.466 Y115.52 E.01074
G1 X119.466 Y116.132 E.02029
G1 X119.142 Y116.132 E.01074
G1 X119.142 Y115.58 E.0183
M204 S10000
G1 X118.735 Y115.113 F42000
G1 F1200
M204 S6000
G1 X119.873 Y115.113 E.03775
G1 X119.873 Y116.539 E.0473
G1 X118.735 Y116.539 E.03775
G1 X118.735 Y115.173 E.04531
M204 S250
G1 X118.343 Y114.721 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.23 Y114.721 E.05798
G1 X120.265 Y114.965 E.00758
G1 X120.26 Y116.931 E.0604
G1 X118.343 Y116.931 E.05891
G1 X118.343 Y114.781 E.06606
; WIPE_START
G1 F3600
M204 S6000
G1 X120.23 Y114.721 E-.71742
G1 X120.246 Y114.832 E-.04258
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z15.8 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z15.8
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z15.8 F4000
            G39.3 S1
            G0 Z15.8 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




; CHANGE_LAYER
; Z_HEIGHT: 15.6
; LAYER_HEIGHT: 0.200001
; layer num/total_layer_count: 78/79
; update layer progress
M73 L78
M991 S0 P77 ;notify layer change
; OBJECT_ID: 105
G1 X118.887 Y115.308 F42000
G1 Z15.6
G1 E.8 F1800
; FEATURE: Inner wall
; LINE_WIDTH: 0.45
G1 F1200
M204 S6000
G1 X119.873 Y115.308 E.0327
G1 X119.873 Y116.454 E.03801
G1 X118.887 Y116.454 E.0327
G1 X118.887 Y115.368 E.03602
M204 S250
G1 X118.495 Y114.916 F42000
; FEATURE: Outer wall
; LINE_WIDTH: 0.42
G1 F1200
M204 S5000
G1 X120.258 Y114.916 E.05417
G1 X120.265 Y114.965 E.00152
G1 X120.265 Y116.846 E.0578
G1 X118.495 Y116.846 E.05439
G1 X118.495 Y114.976 E.05746
; WIPE_START
G1 F3600
M204 S6000
G1 X120.258 Y114.916 E-.67032
G1 X120.265 Y114.965 E-.01881
G1 X120.265 Y115.152 E-.07086
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z16 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z16
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z16 F4000
            G39.3 S1
            G0 Z16 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




; CHANGE_LAYER
; Z_HEIGHT: 15.8
; LAYER_HEIGHT: 0.2
; layer num/total_layer_count: 79/79
; update layer progress
M73 L79
M991 S0 P78 ;notify layer change
; OBJECT_ID: 105
G1 X118.647 Y115.111 F42000
G1 Z15.8
G1 E.8 F1800
G1 F1200
M204 S5000
G1 X120.265 Y115.111 E.04972
G1 X120.265 Y116.761 E.0507
G1 X118.647 Y116.761 E.04972
G1 X118.647 Y115.171 E.04886
; WIPE_START
G1 F3600
M204 S6000
G1 X120.265 Y115.111 E-.61527
G1 X120.265 Y115.492 E-.14473
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z16.2 I1.217 J0 P1  F42000
;===================== date: 20250206 =====================

; don't support timelapse gcode in spiral_mode and by object sequence for I3 structure printer
; SKIPPABLE_START
; SKIPTYPE: timelapse
M622.1 S1 ; for prev firmware, default turned on
M1002 judge_flag timelapse_record_flag
M622 J1
G92 E0
G1 Z16.2
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos
M400
M1004 S5 P1  ; external shutter
M400 P300
M971 S11 C11 O0
G92 E0
G1 X0 F18000
M623

; SKIPTYPE: head_wrap_detect
M622.1 S1
M1002 judge_flag g39_3rd_layer_detect_flag
M622 J1
    ; enable nozzle clog detect at 3rd layer
    


    M622.1 S1
    M1002 judge_flag g39_detection_flag
    M622 J1
      
        M622.1 S0
        M1002 judge_flag g39_mass_exceed_flag
        M622 J1
        
            G392 S0
            M400
            G90
            M83
            M204 S5000
            G0 Z16.2 F4000
            G39.3 S1
            G0 Z16.2 F4000
            G392 S0
          
        M623
    
    M623
M623
; SKIPPABLE_END




G1 X120.058 Y116.058 F42000
G1 Z15.8
G1 E.8 F1800
; FEATURE: Top surface
G1 F1200
M204 S2000
G1 X119.318 Y115.319 E.03214
G1 X118.854 Y115.388
G1 X120.02 Y116.554 E.05065
G1 X119.487 Y116.554
G1 X118.854 Y115.922 E.02748
; close powerlost recovery
M1003 S0
; WIPE_START
G1 F9547.055
M204 S6000
G1 X119.487 Y116.554 E-.3398
G1 X120.02 Y116.554 E-.20264
G1 X119.615 Y116.149 E-.21756
; WIPE_END
G1 E-.04 F1800
M204 S10000
G17
G3 Z16.2 I1.217 J0 P1  F42000
M106 S0
M981 S0 P20000 ; close spaghetti detector
; FEATURE: Custom
; MACHINE_END_GCODE_START
; filament end gcode 

;===== date: 20260513 =====================
;turn off nozzle clog detect
G392 S0

M400 ; wait for buffer to clear
G92 E0 ; zero the extruder
G90
G1 Z16.2 F900 ; lower z a little
G1 X0 Y90 F18000 ; move to safe pos
G1 X-13.0 F3000 ; move to safe pos

M1002 judge_flag timelapse_record_flag
M622 J1
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M400 P100
M971 S11 C11 O0
M991 S0 P-1 ;end timelapse at safe pos
M623


M140 S0 ; turn off bed
M106 S0 ; turn off fan
M106 P2 S0 ; turn off remote part cooling fan
M106 P3 S0 ; turn off chamber cooling fan

;G1 X27 F15000 ; wipe

; pull back filament to AMS
M620 S255
G1 X181 F12000
T255
G1 X0 F18000
G1 X-13.0 F3000
G1 X0 F18000 ; wipe
M621 S255

M104 S0 ; turn off hotend

M400 ; wait all motion done
M17 S
M17 Z0.4 ; lower z motor current to reduce impact if there is something in the bottom

    G1 Z115.8 F600
    G1 Z113.8

M400 P100
M17 R ; restore z current

G90
G1 X-13 Y180 F3600

G91
G1 Z-1 F600
G90
M83

M220 S100  ; Reset feedrate magnitude
M201.2 K1.0 ; Reset acc magnitude
M73.2   R1.0 ;Reset left time magnitude
M1002 set_gcode_claim_speed_level : 0

;=====printer finish  sound=========
M17
M400 S1
M1006 S1
M1006 A0 B20 L100 C37 D20 M100 E42 F20 N100
M1006 A0 B10 L100 C44 D10 M100 E44 F10 N100
M1006 A0 B10 L100 C46 D10 M100 E46 F10 N100
M1006 A44 B20 L100 C39 D20 M100 E48 F20 N100
M1006 A0 B10 L100 C44 D10 M100 E44 F10 N100
M1006 A0 B10 L100 C0 D10 M100 E0 F10 N100
M1006 A0 B10 L100 C39 D10 M100 E39 F10 N100
M1006 A0 B10 L100 C0 D10 M100 E0 F10 N100
M1006 A0 B10 L100 C44 D10 M100 E44 F10 N100
M1006 A0 B10 L100 C0 D10 M100 E0 F10 N100
M1006 A0 B10 L100 C39 D10 M100 E39 F10 N100
M1006 A0 B10 L100 C0 D10 M100 E0 F10 N100
M1006 A44 B10 L100 C0 D10 M100 E48 F10 N100
M1006 A0 B10 L100 C0 D10 M100 E0 F10 N100
M1006 A44 B20 L100 C41 D20 M100 E49 F20 N100
M1006 A0 B20 L100 C0 D20 M100 E0 F20 N100
M1006 A0 B20 L100 C37 D20 M100 E37 F20 N100
M1006 W
;=====printer finish  sound=========
M400 S1
M18 X Y Z
M73 P100 R0
; EXECUTABLE_BLOCK_END

