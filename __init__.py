bl_info = {
    "name": "HERBIE - UV Organizer",
    "author": "HERBIE Dev",
    "version": (1, 4),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > HERBIE",
    "description": "Cube projection, empaque con escala por material, desplazamiento y colores random en UV.",
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


class HERBIE_PT_Panel(bpy.types.Panel):
    bl_label = "HERBIE UVs"
    bl_idname = "HERBIE_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HERBIE'

    def draw(self, context):
        layout = self.layout
        props = context.scene.herbie_props

        layout.prop(props, "pack_margin")
        layout.prop(props, "show_material_colors", text="Color Random por Material", toggle=True)
        layout.separator()
        layout.operator("uv.herbie_organize", text="Organizar UVs por Material")


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
        
        # Guardar estado de UV Sync y apagarlo temporalmente para evitar conflictos
        original_sync = context.scene.tool_settings.use_uv_select_sync
        context.scene.tool_settings.use_uv_select_sync = False
        
        # 1. Identificar materiales realmente en uso inspeccionando polígonos
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

        # 2. Entrar a Edit Mode y aplicar Cube Projection a todo el objeto
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        
        # Seleccionar todas las caras
        for face in bm.faces:
            face.select = True
        bmesh.update_edit_mesh(obj.data)
        
        bpy.ops.uv.cube_project()

        # 3. Localizar un área de Image Editor para Context Override en pack_islands
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

        # 4. Procesar material por material
        for position_index, mat_idx in enumerate(sorted_active_materials, start=1):
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()

            # Seleccionar solo caras de este material
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

            # Desplazamiento matemático directo en el BMesh
            move_x = offset_step * position_index
            bm = bmesh.from_edit_mesh(obj.data)
            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                if face.select:
                    for loop in face.loops:
                        loop[uv_layer].uv.x += move_x

            bmesh.update_edit_mesh(obj.data)

        # Restaurar área original si fue modificada
        if restructure_area:
            context.area.type = 'VIEW_3D'

        # Limpiar selección final
        bm = bmesh.from_edit_mesh(obj.data)
        for face in bm.faces:
            face.select = False
        bmesh.update_edit_mesh(obj.data)

        # Restaurar configuración original
        context.scene.tool_settings.use_uv_select_sync = original_sync
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"HERBIE organizó {len(sorted_active_materials)} materiales exitosamente.")
        return {'FINISHED'}


# Función que dibuja los colores mediante GPU
def draw_uv_colors():
    context = bpy.context
    
    # Validaciones de estado
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

    # Genera un color pseudoaleatorio consistente basado en el índice
    def get_color(idx):
        random.seed(idx + 100)
        return (random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), 0.4)

    for face in bm.faces:
        mat_idx = face.material_index
        col = get_color(mat_idx)
        
        # Triangulación en abanico (fan) para renderizado
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
    
    # Dibujar respetando transparencia (Alpha)
    gpu.state.blend_set('ALPHA')
    shader.bind()
    batch.draw(shader)
    gpu.state.blend_set('NONE')


def register():
    bpy.utils.register_class(HERBIE_Properties)
    bpy.types.Scene.herbie_props = bpy.props.PointerProperty(type=HERBIE_Properties)
    bpy.utils.register_class(HERBIE_PT_Panel)
    bpy.utils.register_class(HERBIE_OT_OrganizeUVs)
    
    # Registrar el callback del GPU para el UV Editor
    global _herbie_draw_handler
    _herbie_draw_handler = bpy.types.SpaceImageEditor.draw_handler_add(draw_uv_colors, (), 'WINDOW', 'POST_VIEW')

def unregister():
    # Remover el callback del GPU
    global _herbie_draw_handler
    if _herbie_draw_handler is not None:
        bpy.types.SpaceImageEditor.draw_handler_remove(_herbie_draw_handler, 'WINDOW')
        _herbie_draw_handler = None

    bpy.utils.unregister_class(HERBIE_OT_OrganizeUVs)
    bpy.utils.unregister_class(HERBIE_PT_Panel)
    del bpy.types.Scene.herbie_props
    bpy.utils.unregister_class(HERBIE_Properties)

if __name__ == "__main__":
    register()