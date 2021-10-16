import bpy
from Sollumz.sollumz_properties import BoundType, PolygonType, ObjectType, MaterialType, is_sollum_type
from Sollumz.ybn.ui import draw_bound_properties, draw_collision_material_properties
from Sollumz.ydr.ui import draw_drawable_properties, draw_geometry_properties, draw_shader

SOLLUMZ_UI_NAMES = {
    BoundType.BOX: 'Bound Box',
    BoundType.SPHERE: 'Bound Sphere',
    BoundType.CAPSULE: 'Bound Capsule',
    BoundType.CYLINDER: 'Bound Cylinder',
    BoundType.DISC: 'Bound Disc',
    BoundType.CLOTH: 'Bound Cloth',
    BoundType.GEOMETRY: 'Bound Geometry',
    BoundType.GEOMETRYBVH: 'GeometryBVH',
    BoundType.COMPOSITE: 'Composite',

    PolygonType.BOX: 'Bound Poly Box',
    PolygonType.SPHERE: 'Bound Poly Sphere',
    PolygonType.CAPSULE: 'Bound Poly Capsule',
    PolygonType.CYLINDER: 'Bound Poly Cylinder',
    PolygonType.TRIANGLE: 'Bound Poly Mesh',
}

class SOLLUMZ_PT_MAT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAT_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # mat = context.active_object.active_material
        return True

    def draw(self, context):
        layout = self.layout

        if(context.active_object == None):
            return

        mat = None
        mat = context.active_object.active_material
        print('test')

        if(mat == None):
            return 

        if mat.sollum_type == MaterialType.MATERIAL:
            draw_shader(layout, mat)
        elif mat.sollum_type == MaterialType.COLLISION:
            draw_collision_material_properties(layout, mat)


class SOLLUMZ_PT_OBJECT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAIN_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw_drawable_model_properties(self, context, layout, obj):
        layout.prop(obj.drawable_model_properties, "render_mask")
        layout.prop(obj.drawable_model_properties, "flags")
        layout.prop(obj.drawable_model_properties, "sollum_lod")

    
    def draw(self, context):
        layout = self.layout

        obj = bpy.context.active_object

        if(obj == None):
            return

        box = layout.box()
        row = box.row()
        row.enabled = False
        row.prop(obj, "sollum_type")

        try:
            getattr(obj, 'sollum_type')
        except:
            return

        if obj.sollum_type == ObjectType.DRAWABLE:
            draw_drawable_properties(box, obj)
        elif obj.sollum_type == ObjectType.GEOMETRY:
            draw_geometry_properties(box, obj)
        elif(obj.sollum_type == ObjectType.DRAWABLE_MODEL):
            self.draw_drawable_model_properties(context, box, obj)
        elif is_sollum_type(obj, BoundType):
            draw_bound_properties(box, obj)

class SOLLUMZ_MT_sollumz(bpy.types.Menu):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_MT_sollumz"

    def draw(self, context):
        layout = self.layout

def SollumzContextMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_sollumz.bl_idname)

class SOLLUMZ_MT_create(bpy.types.Menu):
    bl_label = "Create"
    bl_idname = "SOLLUMZ_MT_create"

    def draw(self, context):
        layout = self.layout

def SollumzCreateContextMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_create.bl_idname)
    

def register():
    bpy.types.VIEW3D_MT_mesh_add.append(SollumzContextMenu)
    bpy.types.SOLLUMZ_MT_sollumz.append(SollumzCreateContextMenu)

def unregister():
    bpy.types.SOLLUMZ_MT_sollumz.remove(SollumzCreateContextMenu)
    bpy.types.VIEW3D_MT_mesh_add.remove(SollumzContextMenu)