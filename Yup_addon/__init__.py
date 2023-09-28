# original code by rraallvv

bl_info = {
    "name" : "Yup",
    "author" : "viatrufka",
    "description" : "",
    "blender" : (3, 6, 0),
    "version" : (1,0),
    'location': '3d view > MMB-drag',
    'description': 'Enable turntable rotation with Y axis up.',
    'wiki_url': '',
    'tracker_url': '',
    'category': '3D View'
    }

import bpy
from mathutils import *
from math import *

class RotateTurntableYUp(bpy.types.Operator):
    '''Turntable rotation Y-axis up.'''
    bl_idname = "view3d.turntable_y_up"
    bl_label = "Turntable rotation Y-axis up"
    
    angle_yaw=0
    angle_pitch=0
    mouse_last_pos=Vector((0,0))
    axis_selected=0
    do_alignment=True
    
    def execute(self, context):
        region_3d = context.space_data.region_3d
                
        # world axis in world space
        xa=Vector((1,0,0))
        ya=Vector((0,1,0))
        za=Vector((0,0,1))
                
        # select Y axis to alignt the camera
        camera_up_axis=ya.copy()
        camera_up_axis.rotate(region_3d.view_rotation.inverted())
        world_up_axis=ya
                
        # find rotation yaw in camera space, rotation yaw in world space, separation angle 
        # between them, and the rotation needed to align the camera axis up in the world space
        if camera_up_axis.y > 0:
            camera_rotation_yaw=Quaternion(camera_up_axis,self.angle_yaw)
            world_rotation_yaw=Quaternion(world_up_axis,self.angle_yaw)
            separation_angle=atan2(camera_up_axis.y,camera_up_axis.x)-pi*0.5
            rotation_alignment=Quaternion(za,separation_angle)
        
        elif camera_up_axis.y < 0:
            camera_rotation_yaw=Quaternion(camera_up_axis,-self.angle_yaw)
            world_rotation_yaw=Quaternion(world_up_axis,-self.angle_yaw)
            separation_angle=atan2(camera_up_axis.y,camera_up_axis.x)+pi*0.5
            rotation_alignment=Quaternion(za,separation_angle)
        else:
            camera_rotation_yaw=Quaternion((0,0,0,1))
            world_rotation_yaw=Quaternion((0,0,0,1))
            separation_angle = 0
            rotation_alignment=Quaternion((0,0,0,1))
       
        # check if there are selected objects in case of the user preference
        #  to rotate around the selection pivot
        selected_objects = len(bpy.context.selected_objects) > 0 and bpy.context.preferences.inputs.use_rotate_around_active
                
        # find the pivot point location
        if selected_objects:
            saved_location = bpy.context.scene.cursor_location.copy()
            bpy.ops.view3d.snap_cursor_to_selected()
            pivot_location = bpy.context.scene.cursor_location.copy()
            bpy.context.scene.cursor_location = saved_location


        # rotate the view_location and view_rotation to perform the turn table rotation
                
        if self.do_alignment:
            # on invocation rotate the view_location to avoid the origin or the pivot to jump abruptly
            if selected_objects:
                region_3d.view_location=region_3d.view_location-pivot_location
            
            region_3d.view_rotation=region_3d.view_rotation@Quaternion(za, separation_angle)
            camera_normal_axis=za
            camera_normal_axis.rotate(region_3d.view_rotation)

            region_3d.view_location.rotate(Quaternion(camera_normal_axis, separation_angle))
            
            if selected_objects:
                region_3d.view_location=region_3d.view_location+pivot_location
        
            self.do_alignment=False
        else:
            # oterwise do the alignment
            region_3d.view_rotation = region_3d.view_rotation @ rotation_alignment
        
        # compensate the rotation is there is objects selected, to rotate around the pivot point
        if selected_objects:
            camera_horizontal_axis=xa.copy()
            camera_horizontal_axis.rotate(region_3d.view_rotation)
            
            world_rotation_pitch=Quaternion(camera_horizontal_axis,self.angle_pitch)
            
            pivot_to_camera = region_3d.view_location - pivot_location
            pivot_to_camera.rotate(world_rotation_yaw@world_rotation_pitch)
            
            region_3d.view_location = pivot_location + pivot_to_camera
        
        
        # find rotation pitch in camera space
        camera_rotation_pitch=Quaternion(xa,self.angle_pitch)
        #print(camera_rotation_yaw)
        print(camera_rotation_yaw,camera_rotation_pitch)
        region_3d.view_rotation=region_3d.view_rotation@camera_rotation_yaw@camera_rotation_pitch
        #custom_rotation = Quaternion((2, 0.2, 0, 0.5))
        #region_3d.view_rotation = custom_rotation
        #print(region_3d.view_rotation)
        return {'FINISHED'}
    
    def modal(self, context, event):
        
        if event.type == 'MOUSEMOVE':
            #find the yaw and pitch angles from the mouse position variation
            mouse_pos=Vector((event.mouse_region_x,event.mouse_region_y))
            self.angle_yaw=-(mouse_pos.x-self.mouse_last_pos.x)/200.0
            self.angle_pitch=(mouse_pos.y-self.mouse_last_pos.y)/200.0
            print(self.angle_yaw, self.angle_pitch)
            self.execute(context)
            self.mouse_last_pos=Vector((event.mouse_region_x,event.mouse_region_y))
        
        elif event.type in {'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'ESC'}:
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        
        if context.space_data.type == 'VIEW_3D':
            region_3d = context.space_data.region_3d
            self.mouse_last_pos=Vector((event.mouse_region_x,event.mouse_region_y))
            
            self.axis_selected=0
            self.do_alignment=True
            
            context.window_manager.modal_handler_add(self)
            
            if region_3d.view_perspective == 'CAMERA':
                region_3d.view_perspective = 'PERSP'
            
            return {'RUNNING_MODAL'}
        
        else:
            return {'CANCELLED'}


def menu_func(self, context):
    self.layout.operator(RotateTurntableYUp.bl_idname, text=RotateTurntableYUp.bl_label)
    
def register():
    bpy.utils.register_class(RotateTurntableYUp)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    wm = bpy.context.window_manager
    
    km = wm.keyconfigs.addon.keymaps.new(name="3D View", space_type='VIEW_3D')
    kmi = km.keymap_items.new('view3d.turntable_y_up', 'MIDDLEMOUSE', 'ANY', shift=False, ctrl=False, alt=False)
    
def unregister():
    bpy.utils.unregister_class(RotateTurntableYUp)
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps['3D View']
    for kmi in km.keymap_items:
        if kmi.idname == 'view3d.turntable_y_up':
            km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
