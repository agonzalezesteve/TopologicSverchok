import bpy
from bpy.props import IntProperty, FloatProperty, StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

import topologic
from topologic import Vertex, Edge, Wire, Face, Shell, Cell, CellComplex, Cluster, Topology
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

def repeat(list):
	maxLength = len(list[0])
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		if (len(anItem) > 0):
			itemToAppend = anItem[-1]
		else:
			itemToAppend = None
		for i in range(len(anItem), maxLength):
			anItem.append(itemToAppend)
	return list

# From https://stackoverflow.com/questions/34432056/repeat-elements-of-list-between-each-other-until-we-reach-a-certain-length
def onestep(cur,y,base):
    # one step of the iteration
    if cur is not None:
        y.append(cur)
        base.append(cur)
    else:
        y.append(base[0])  # append is simplest, for now
        base = base[1:]+[base[0]]  # rotate
    return base

def iterate(list):
	maxLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength > maxLength:
			maxLength = newLength
	for anItem in list:
		for i in range(len(anItem), maxLength):
			anItem.append(None)
		y=[]
		base=[]
		for cur in anItem:
			base = onestep(cur,y,base)
			# print(base,y)
		returnList.append(y)
	return returnList

def trim(list):
	minLength = len(list[0])
	returnList = []
	for aSubList in list:
		newLength = len(aSubList)
		if newLength < minLength:
			minLength = newLength
	for anItem in list:
		anItem = anItem[:minLength]
		returnList.append(anItem)
	return returnList

# Adapted from https://stackoverflow.com/questions/533905/get-the-cartesian-product-of-a-series-of-lists
def interlace(ar_list):
    if not ar_list:
        yield []
    else:
        for a in ar_list[0]:
            for prod in interlace(ar_list[1:]):
                yield [a,]+prod

def transposeList(l):
	length = len(l[0])
	returnList = []
	for i in range(length):
		tempRow = []
		for j in range(len(l)):
			tempRow.append(l[j][i])
		returnList.append(tempRow)
	return returnList

def processItem(item):
	gc = topologic.GlobalCluster.GetInstance()
	subTopologies = []
	_ = gc.SubTopologies(subTopologies)
	for aSubTopology in subTopologies:
		gc.RemoveTopology(aSubTopology)
	return item

class SvGlobalClusterClear(bpy.types.Node, SverchCustomTreeNode):
	"""
	Triggers: Topologic
	Tooltip: Clears the Global Cluster    
	"""
	bl_idname = 'SvGlobalClusterClear'
	bl_label = 'GlobalCluster.Clear'

	def sv_init(self, context):
		self.inputs.new('SvStringsSocket', 'Wait For')
		self.outputs.new('SvStringsSocket', 'Pass Through')

	def process(self):
		start = time.time()
		if not any(socket.is_linked for socket in self.inputs):
			return
		waitForList = self.inputs['Wait For'].sv_get(deepcopy=True)
		waitForList = flatten(waitForList)
		outputs = []
		if(len(waitForList) > 0):
			for anInput in waitForList:
				outputs.append(processItem(anInput))
		else:
			outputs.append(processItem(None))
		self.outputs['Pass Through'].sv_set(outputs)
		end = time.time()
		print("GlobalCluster.Clear Operation consumed "+str(round(end - start,2)*1000)+" ms")

def register():
	bpy.utils.register_class(SvGlobalClusterClear)

def unregister():
	bpy.utils.unregister_class(SvGlobalClusterClear)
