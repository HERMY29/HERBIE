bl_info = {
    "name": "HERBIE - UV Organizer",
    "author": "HERBIE Dev",
    "version": (1, 5),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > HERBIE",
    "description": "Herramientas de mapeo y empaque automático de UVs por material.",
    "category": "UV",
}

import bpy
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
import random

# Variables globales para el manejador de dibujo
_herbie_draw_handler = None


class HERBIE_Properties(bpy.types.PropertyGroup):
    # Propiedades originales
    pack_margin: bpy.props.FloatProperty(
        name="Pack Margin",
        description="Margen entre islas al empacar",
        default=0.03,
        min=0.0,
        max=1.0,
        precision=3
    )
    
    show_material_colors: bpy.props.BoolProperty(
        name="Mostrar Colores por Material",
        description="Dibuja colores aleatorios por material en el UV Editor",
        default=False
    )
    
    # Nuevas propiedades para proyección
    mapping_type: bpy.props.EnumProperty(
        name="Método",
        description="Tipo de proyección a aplicar",
        items=[
            ('CUBE', "Cube Projection", ""),
            ('CYLINDER', "Cylinder Projection", ""),
            ('SPHERE', "Sphere Projection", ""),
            ('VIEW', "Project from View", ""),
            ('VIEW_BOUNDS', "Project from View (Bounds)", "")
        ],
        default='CUBE'
    )
    
    cube_size: bpy.props.FloatProperty(name="Cube Size", default=1.0, min=0.001)
    cyl_radius: bpy.props.FloatProperty(name="Radius", default=1.0, min=0.001)
    correct_aspect: bpy.props.BoolProperty(name="Correct Aspect", default=True)
    scale_to_bounds: bpy.props.BoolProperty(name="Scale to Bounds", default=False)


class HERBIE_PT_Panel(bpy.types.Panel):
    bl_label = "HERBIE UVs"
    bl_idname = "HERBIE_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HERBIE'

    def draw(self, context):
        layout = self.layout
        props = context.scene.herbie_props

        # Sección 1: Proyección Manual
        layout.label(text="Proyección Rápida:")
        layout.prop(props, "mapping_type")
        
        box = layout.box()
        if props.mapping_type == 'CUBE':
            box.prop(props, "cube_size")
            box.prop(props, "correct_aspect")
            box.prop(props, "scale_to_bounds")
        elif props.mapping_type == 'CYLINDER':
            box.prop(props, "cyl_radius")
            box.prop(props, "correct_aspect")
            box.prop(props, "scale_to_bounds")
        elif props.mapping_type == 'SPHERE':
            box.prop(props, "correct_aspect")
            box.prop(props, "scale_to_bounds")
        elif props.mapping_type == 'VIEW':
            box.prop(props, "correct_aspect")
            box.prop(props, "scale_to_bounds")
        elif props.mapping_type == 'VIEW_BOUNDS':
            box.prop(props, "correct_aspect")
            
        layout.operator("uv.herbie_apply_mapping", text="Aplicar Proyección", icon='MOD_UVPROJECT')
        
        layout.separator()
        layout.separator()

        # Sección 2: Organización y Colores
        layout.label(text="Organización por Material:")
        layout.prop(props, "pack_margin")
        layout.operator("uv.herbie_organize", text="Organizar UVs por Material", icon='UV_ISLANDSEL')
        layout.prop(props, "show_material_colors", text="Color Random por Material", toggle=True)


class HERBIE_OT_ApplyMapping(bpy.types.Operator):
    bl_idname = "uv.herbie_apply_mapping"
    bl_label = "Aplicar Proyección (HERBIE)"
    bl_description = "Aplica la proyección configurada. Afecta selección en Edit Mode o a todos los objetos seleccionados en Object Mode"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        props = context.scene.herbie_props
        initial_mode = context.active_object.mode
        
        # Si estamos en Object Mode, preparar todos los objetos seleccionados
        if initial_mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type="FACE")
            bpy.ops.mesh.select_all(action='SELECT')
        
        # Aplicar el operador de proyección correspondiente
        try:
            if props.mapping_type == 'CUBE':
                bpy.ops.uv.cube_project(
                    cube_size=props.cube_size,
                    correct_aspect=props.correct_aspect,
                    scale_to_bounds=props.scale_to_bounds
                )
            elif props.mapping_type == 'CYLINDER':
                bpy.ops.uv.cylinder_project(
                    radius=props.cyl_radius,
                    correct_aspect=props.correct_aspect,
                    scale_to_bounds=props.scale_to_bounds
                )
            elif props.mapping_type == 'SPHERE':
                bpy.ops.uv.sphere_project(
                    correct_aspect=props.correct_aspect,
                    scale_to_bounds=props.scale_to_bounds
                )
            elif props.mapping_type == 'VIEW':
                bpy.ops.uv.project_from_view(
                    camera_bounds=False,
                    correct_aspect=props.correct_aspect,
                    scale_to_bounds=props.scale_to_bounds
                )
            elif props.mapping_type == 'VIEW_BOUNDS':
                bpy.ops.uv.project_from_view(
                    camera_bounds=False,
                    correct_aspect=props.correct_aspect,
                    scale_to_bounds=True
                )
        except Exception as e:
            self.report({'ERROR'}, f"Fallo al aplicar proyección: {e}")
            return {'CANCELLED'}
            
        # Restaurar a Object Mode si se inició desde ahí
        if initial_mode == 'OBJECT':
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            
        self.report({'INFO'}, "Proyección aplicada exitosamente")
        return {'FINISHED'}


class HERBIE_OT_OrganizeUVs(bpy.types.Operator):
    bl_idname = "uv.herbie_organize"
    bl_label = "Organizar UVs (HERBIE)"
    bl_description = "Cube projection, empaque con escala por material y desplazamiento compacto"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        props = context.scene.herbie_props
        
        original_sync = context.scene.tool_settings.use_uv_select_sync
        context.scene.tool_settings.use_uv_select_sync = False
        
        bpy.ops.object.mode_set(mode='OBJECT')
        used_materials = set()
        for poly in obj.data.polygons:
            if poly.material_index < len(obj.material_slots):
                used_materials.add(poly.material_index)
                
        if not used_materials:
            context.scene.tool_settings.use_uv_select_sync = original_sync
            self.report({'WARNING'}, "El objeto no tiene materiales asignados en uso.")
            return {'CANCELLED'}

        sorted_active_materials = sorted(list(used_materials))

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        
        for face in bm.faces:
            face.select = True
        bmesh.update_edit_mesh(obj.data)
        
        bpy.ops.uv.cube_project()

        uv_area = None
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                uv_area = area
                break

        restructure_area = False
        if uv_area is None:
            context.area.type = 'IMAGE_EDITOR'
            uv_area = context.area
            restructure_area = True

        uv_region = [r for r in uv_area.regions if r.type == 'WINDOW'][0]
        offset_step = 1.1

        for position_index, mat_idx in enumerate(sorted_active_materials, start=1):
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                is_target = (face.material_index == mat_idx)
                face.select = is_target
            bmesh.update_edit_mesh(obj.data)

            override = {
                'window': context.window,
                'screen': context.screen,
                'area': uv_area,
                'region': uv_region,
                'scene': context.scene,
                'active_object': obj,
                'edit_object': obj,
                'selectable_objects': [obj],
                'selected_objects': [obj],
            }

            try:
                if hasattr(context, "temp_override"):
                    with context.temp_override(**override):
                        bpy.ops.uv.select_all(action='SELECT') 
                        bpy.ops.uv.pack_islands(margin=props.pack_margin, scale=True, rotate=False)
                else:
                    bpy.ops.uv.select_all(override, action='SELECT')
                    bpy.ops.uv.pack_islands(override, margin=props.pack_margin, scale=True, rotate=False)
            except Exception as e:
                self.report({'WARNING'}, f"Fallo al empacar material {mat_idx}: {e}")

            move_x = offset_step * position_index
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                if face.select:
                    for loop in face.loops:
                        loop[uv_layer].uv.x += move_x

            bmesh.update_edit_mesh(obj.data)

        if restructure_area:
            context.area.type = 'VIEW_3D'

        bm = bmesh.from_edit_mesh(obj.data)
        for face in bm.faces:
            face.select = False
        bmesh.update_edit_mesh(obj.data)

        context.scene.tool_settings.use_uv_select_sync = original_sync
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"HERBIE organizó {len(sorted_active_materials)} materiales exitosamente.")
        return {'FINISHED'}


def draw_uv_colors():
    context = bpy.context
    
    if not hasattr(context.scene, "herbie_props") or not context.scene.herbie_props.show_material_colors:
        return
        
    obj = context.active_object
    if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
        return
        
    area = context.area
    if not area or area.type != 'IMAGE_EDITOR':
        return

    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.active
    if not uv_layer:
        return

    coords = []
    colors = []

    def get_color(idx):
        random.seed(idx + 100)
        return (random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), 0.4)

    for face in bm.faces:
        mat_idx = face.material_index
        col = get_color(mat_idx)
        
        loops = face.loops
        if len(loops) >= 3:
            uv0 = loops[0][uv_layer].uv
            for i in range(1, len(loops) - 1):
                coords.append((uv0.x, uv0.y))
                coords.append((loops[i][uv_layer].uv.x, loops[i][uv_layer].uv.y))
                coords.append((loops[i+1][uv_layer].uv.x, loops[i+1][uv_layer].uv.y))
                
                colors.append(col)
                colors.append(col)
                colors.append(col)

    if not coords:
        return

    try:
        shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    except ValueError:
        shader = gpu.shader.from_builtin('SMOOTH_COLOR')
        
    batch = batch_for_shader(shader, 'TRIS', {"pos": coords, "color": colors})
    
    gpu.state.blend_set('ALPHA')
    shader.bind()
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def register():
    bpy.utils.register_class(HERBIE_Properties)
    bpy.types.Scene.herbie_props = bpy.props.PointerProperty(type=HERBIE_Properties)
    bpy.utils.register_class(HERBIE_PT_Panel)
    bpy.utils.register_class(HERBIE_OT_OrganizeUVs)
    bpy.utils.register_class(HERBIE_OT_ApplyMapping)
    
    global _herbie_draw_handler
    _herbie_draw_handler = bpy.types.SpaceImageEditor.draw_handler_add(draw_uv_colors, (), 'WINDOW', 'POST_VIEW')

def unregister():
    global _herbie_draw_handler
    if _herbie_draw_handler is not None:
        bpy.types.SpaceImageEditor.draw_handler_remove(_herbie_draw_handler, 'WINDOW')
        _herbie_draw_handler = None

    bpy.utils.unregister_class(HERBIE_OT_ApplyMapping)
    bpy.utils.unregister_class(HERBIE_OT_OrganizeUVs)
    bpy.utils.unregister_class(HERBIE_PT_Panel)
    del bpy.types.Scene.herbie_props
    bpy.utils.unregister_class(HERBIE_Properties)

if __name__ == "__main__":
    register()