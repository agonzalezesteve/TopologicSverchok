import bpy
from bpy.props import StringProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
import cppyy
# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def processItem(faces, tol):
	stl_faces = cppyy.gbl.std.list[topologic.Face.Ptr]()
	for face in faces:
		stl_faces.push_back(face)
	shell = topologic.Shell.ByFaces(stl_faces, tol)
	vertices = cppyy.gbl.std.list[topologic.Vertex.Ptr]()
	try:
		_ = shell.Vertices(vertices)
	except:
		raise Exception("Error: Could not create a valid Shell. Please check input.")
	if len(vertices) < 3:
		raise Exception("Error: Could not create a valid Shell. Please check input.")
	return shell

class SvShellByFaces(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Creates a Shell from the list of input Faces  
	"""
	bl_idname = 'SvShellByFaces'
	bl_label = 'Shell.ByFaces'
	Tol: FloatProperty(name='Tol', default=0.0001, precision=4, update=updateNode)

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Faces')
		self.inputs.new('SvStringsSocket', 'Tol').prop_name='Tol'
		self.outputs.new('SvStringsSocket', 'Shell')

	def process(self):
		if not any(socket.is_linked for socket in self.outputs):
			return
		faceList = self.inputs['Faces'].sv_get(deepcopy=False)
		tol = self.inputs['Tol'].sv_get(deepcopy=True, default=0.0001)[0][0]
		if isinstance(faceList[0], list) == False:
			faceList = [faceList]
		output = []
		for faces in faceList:
			output.append(processItem(faces, tol))
		self.outputs['Shell'].sv_set(output)

def register():
    bpy.utils.register_class(SvShellByFaces)

def unregister():
    bpy.utils.unregister_class(SvShellByFaces)
