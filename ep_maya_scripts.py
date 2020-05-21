import maya.cmds as cmds

def clear_keys():
    cmds.select("BS_node")
    for i in range(180):
        cmds.cutKey(cl=True)

def keyframe_expressions(expressions):
    cmds.select("BS_node")
    for i in range(len(expressions)):
        cmds.currentTime(i, update=True)
        reset_blendshapes()
        set_blendshape_by_index(expressions[i])
        cmds.setKeyframe()

def reset_blendshapes():
    root = "BS_node"
    targets = cmds.listAttr(root + ".w",m=True)
    for target in targets:
        cmds.setAttr(root + "." + target,0)

def set_blendshape_by_index(indices):
    root = "BS_node"
    targets = cmds.listAttr(root + ".w",m=True)
    for index in indices:
        cmds.setAttr(root + "." + targets[index], 1)