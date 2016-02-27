ADD_ITEM_RECURSION = True
SYS_TAG_NEW = '[NEW]'
SYS_TAG_DEL = '[DEL]'
TAG_COLOR_AND_SIZE = {SYS_TAG_NEW:('blue', '+5', 'I'),}

def blacklist(filepath):
    if "EvernoteIERes" in filepath : return True
    if "NodeWebKit" in filepath : return True
    if ".zip" == filepath[-4:] : return True
    if ".dll" == filepath[-4:] : return True
    return False    