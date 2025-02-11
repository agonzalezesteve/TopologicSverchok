import bpy
import bmesh
from bpy.props import FloatProperty, StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import uuid
from sverchok.utils.sv_mesh_utils import get_unique_faces

import topologic
from topologic import Topology, Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Graph, Dictionary, Attribute, VertexUtility, EdgeUtility, WireUtility, FaceUtility, ShellUtility, CellUtility, TopologyUtility

import time

# From https://stackabuse.com/python-how-to-flatten-list-of-lists/
def flatten(element):
	returnList = []
	if isinstance(element, list) == True:
		for anItem in element:
			returnList = returnList + flatten(anItem)
	else:
		returnList = [element]
	return returnList

def getSubTopologies(topology, subTopologyClass):
	topologies = []
	if subTopologyClass == Vertex:
		_ = topology.Vertices(None, topologies)
	elif subTopologyClass == Edge:
		_ = topology.Edges(None, topologies)
	elif subTopologyClass == Wire:
		_ = topology.Wires(None, topologies)
	elif subTopologyClass == Face:
		_ = topology.Faces(None, topologies)
	elif subTopologyClass == Shell:
		_ = topology.Shells(None, topologies)
	elif subTopologyClass == Cell:
		_ = topology.Cells(None, topologies)
	elif subTopologyClass == CellComplex:
		_ = topology.CellComplexes(None, topologies)
	return topologies

def triangulate(faces):
	triangles = []
	for aFace in faces:
		ib = []
		_ = aFace.InternalBoundaries(ib)
		if len(ib) != 0:
			faceTriangles = []
			FaceUtility.Triangulate(aFace, 0.0, faceTriangles)
			for aFaceTriangle in faceTriangles:
				triangles.append(aFaceTriangle)
		else:
			triangles.append(aFace)
	return triangles

class SvTopologyGeometry(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Converts the input Topology into a geometry
	"""
	bl_idname = 'SvTopologyGeometry'
	bl_label = 'Topology.Geometry'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Topology')
		self.outputs.new('SvVerticesSocket', 'Vertices')
		self.outputs.new('SvStringsSocket', 'Edges')
		self.outputs.new('SvStringsSocket', 'Faces')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.outputs):
			return
		if not any(socket.is_linked for socket in self.inputs):
			return
		inputs = self.inputs['Topology'].sv_get(deepcopy=True)
		inputs = flatten(inputs)
		finalVertexList = []
		finalEdgeList = []
		finalFaceList = []
		for anInput in inputs:
			vertices = []
			edges = []
			faces = []
			if anInput == None:
				continue
			topVerts = []
			if (anInput.Type() == 1): #input is a vertex, just add it and process it
				topVerts.append(anInput)
			else:
				_ = anInput.Vertices(None, topVerts)
			for aVertex in topVerts:
				try:
					vertices.index([aVertex.X(), aVertex.Y(), aVertex.Z()]) # Vertex already in list
				except:
					vertices.append([aVertex.X(), aVertex.Y(), aVertex.Z()]) # Vertex not in list, add it.
			topEdges = []
			if (anInput.Type() == 2): #Input is an Edge, just add it and process it
				topEdges.append(anInput)
			elif (anInput.Type() > 2):
				_ = anInput.Edges(None, topEdges)
			for anEdge in topEdges:
				e = []
				sv = anEdge.StartVertex()
				ev = anEdge.EndVertex()
				try:
					svIndex = vertices.index([sv.X(), sv.Y(), sv.Z()])
				except:
					vertices.append([sv.X(), sv.Y(), sv.Z()])
					svIndex = len(vertices)-1
				try:
					evIndex = vertices.index([ev.X(), ev.Y(), ev.Z()])
				except:
					vertices.append([ev.X(), ev.Y(), ev.Z()])
					evIndex = len(vertices)-1
				e.append(svIndex)
				e.append(evIndex)
				if ([e[0], e[1]] not in edges) and ([e[1], e[0]] not in edges):
					edges.append(e)
			topFaces = []
			if (anInput.Type() == 8): # Input is a Face, just add it and process it
				topFaces.append(anInput)
			elif (anInput.Type() > 8):
				_ = anInput.Faces(None, topFaces)
			for aFace in topFaces:
				ib = []
				_ = aFace.InternalBoundaries(ib)
				if(len(ib) > 0):
					triFaces = []
					try:
						_ = FaceUtility.Triangulate(aFace, 0.0, triFaces)
						for aTriFace in triFaces:
							wire = aTriFace.ExternalBoundary()
							faceVertices = getSubTopologies(wire, Vertex)
							f = []
							for aVertex in faceVertices:
								try:
									fVertexIndex = vertices.index([aVertex.X(), aVertex.Y(), aVertex.Z()])
								except:
									vertices.append([aVertex.X(), aVertex.Y(), aVertex.Z()])
									fVertexIndex = len(vertices)-1
								f.append(fVertexIndex)
							faces.append(f)
					except:
						continue
				else:
					wire =  aFace.ExternalBoundary()
					#wire = topologic.WireUtility.RemoveCollinearEdges(wire, 0.1) #This is an angle Tolerance
					faceVertices = getSubTopologies(wire, Vertex)
					f = []
					for aVertex in faceVertices:
						try:
							fVertexIndex = vertices.index([aVertex.X(), aVertex.Y(), aVertex.Z()])
						except:
							vertices.append([aVertex.X(), aVertex.Y(), aVertex.Z()])
							fVertexIndex = len(vertices)-1
						f.append(fVertexIndex)
					faces.append(f)
			finalVertexList.append(vertices)
			finalEdgeList.append(edges)
			finalFaceList.append(faces)
		
		#faces = get_unique_faces(faces) #Make sure we do not accidentally have duplicate faces
		self.outputs['Vertices'].sv_set(finalVertexList)
		self.outputs['Edges'].sv_set(finalEdgeList)
		self.outputs['Faces'].sv_set(finalFaceList)
		end = time.time()
		print("Topology.Geometry Operation consumed "+str(round(end - start,2)*1000)+" ms")

def register():
	bpy.utils.register_class(SvTopologyGeometry)

def unregister():
	bpy.utils.unregister_class(SvTopologyGeometry)

