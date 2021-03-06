"""
    Perform visual layout of QuadTree in Tk canvas.

    Layout inspired by https://llimllib.github.io/pymag-trees/
    
    Accepts any structure that has 'children' list attribute with up to
    four child nodes. May still produce some layouts that have overlapping 
    nodes but works for the most part.

    Note: Before use, must externally set the small/large fonts to use, 
    otherwise the default one is likely too small to see.
"""

from quadtree.util import NE, NW, SW, SE
from collections import defaultdict

# Width,height in pixels for the nodes.
node_w = 25
node_h = 25

# Magnification factor to convert abstract positioning from DrawTree into
# actual pixels. Note that width < magx and height < magy otherwise bad
# things happen.
magx = 30
magy = 80

# Inset drawing by 4 pixels on top and left so nodes fully appear
inset = 4

class DrawTree(object):
    """
    Abstract representation of a QuadTree, in preparation for visualization.
    Each DrawTree node is assigned an (x,y) integer pair where y reflects 
    the depth of the node (0=root) and x reflects the offset position within 
    that depth.

    Algorithm inspired by from https://llimllib.github.io/pymag-trees
    """
    
    # must be set externally after tk is initialized.
    smallFont = None
    largeFont = None
    
    
    def __init__(self, qtnode, depth=0, label=None):
        """Recursively construct DrawTree to parallel quadtree node."""
        self.label = label
        self.x = -1
        self.y = depth
        self.mod = 0
        self.node = qtnode
        self.children = [None] * 4

        for quad in range(len(qtnode.children)):
            if qtnode.children[quad] is not None:
                self.children[quad] = DrawTree(qtnode.children[quad], depth+1, label)

    def assign(self, depth, nexts):
        """
        Recursively assign (x,y) abstract values to each node in DrawTree.
        nexts is dictionary for next x-coordinate on given depth.
        """
        x_min = 99999
        x_max = -99999
        
        # place self initially before children, and update next coordinate for node
        # on this same depth level (might not be a direct sibling)
        self.x = nexts[depth]
        nexts[depth] += 2
        self.y = depth
        
        # recursively process descendant nodes, and determine min/max of children.
        for quad in range(len(self.children)):
            if self.children[quad] is not None:
                self.children[quad].assign(depth+1, nexts)
                x_min = min(x_min, self.children[quad].x)
                x_max = max(x_max, self.children[quad].x)
    
        # If no children, do nothing. Key idea is that self.x should be 
        # centered over children. If child_mid is to our left, must modify
        # modify their placement by difference (i.e., mod = self.x - child_mid).
        # This update takes place later during adjust recursion method. In
        # preparation, update nexts[depth+1] to make room.
        # If child_mid is to our right, then we only need to move self into 
        # position and update nexts[depth] to leave room for next nodes @ level.
        if x_min != 99999:
            child_mid = (x_min + x_max) / 2.0
            if child_mid < self.x:
                self.mod = self.x - child_mid
                nexts[depth+1] += self.mod       
            elif child_mid > self.x:
                self.x = child_mid
                nexts[depth] = max(nexts[depth] + 2, self.x + 2)

    def adjust(self, modsum=0):
        """Adjust descendants based on computed 'mod' shift in recursion."""
        self.x += modsum
        modsum += self.mod

        for quad in range(len(self.children)):
            if self.children[quad] is not None:
                self.children[quad].adjust(modsum)       

    def middle(self):
        """Compute mid point for DrawTree node."""
        return (self.x * magx + node_w/2,
                self.y * magy + node_h/2)

    def layout(self):
        """
        Compute the layout for a DrawTree. In first recursive traversal, assign
        abstract coordinates for each node. In second traversal, shift nodes, as 
        needed, based on orientation with regards to their children.
        """
        # use defaultdict (with default of 0) for each level to start at left.
        self.assign(0, defaultdict(int))
        self.adjust(0)

    def format(self, canvas, orientation=-1):
        """
        Create visual representation of node on canvas.
        
        Represent children node with inner colored rectangle as visual cue.
        """
        for quad in range(len(self.children)):
            if self.children[quad] is not None:
                mid = self.middle()
                child = self.children[quad].middle()
                canvas.create_line(inset + mid[0],   inset + mid[1], 
                                   inset + child[0], inset + child[1])
                self.children[quad].format(canvas, quad)

        color = 'white'
        if self.label:
            ival = self.label(self.node)
            if ival == 0:
                color = 'gray'
        canvas.create_rectangle(inset + self.x * magx, 
                                inset + self.y * magy,
                                inset + self.x * magx+node_w, 
                                inset + self.y * magy+node_h, 
                                fill=color)

        # draw corner in faint colors
        if orientation == NW:
            canvas.create_rectangle(inset + self.x * magx,
                                    inset + self.y * magy,
                                    inset + self.x * magx + node_w/2, 
                                    inset + self.y * magy + node_h/2,
                                    fill='#ffcccc')
        elif orientation == NE:
            canvas.create_rectangle(inset + self.x * magx + node_w/2,
                                    inset + self.y * magy,
                                    inset + self.x * magx + node_w, 
                                    inset + self.y * magy + node_h/2,
                                    fill='#ccffcc')
        elif orientation == SW:
            canvas.create_rectangle(inset + self.x * magx,
                                    inset + self.y * magy + node_h/2,
                                    inset + self.x * magx + node_w/2, 
                                    inset + self.y * magy + node_h,
                                    fill='#ccccff')
        elif orientation == SE:
            canvas.create_rectangle(inset + self.x * magx + node_w/2,
                                    inset + self.y * magy + node_h/2,
                                    inset + self.x * magx + node_w, 
                                    inset + self.y * magy + node_h,
                                    fill='#ccffff')

        # use small font for values 10 and higher.
        font = DrawTree.largeFont
        text = ''
        if self.label:
            ival = self.label(self.node)
            text = str(ival)
            if ival > 9:
                font = DrawTree.smallFont
        
        canvas.create_text(inset + self.x * magx + node_w/2,
                           inset + self.y * magy + node_h/2,
                           font=font,
                           width=node_w, text=text)

    def indent(self, tab):
        """Helper method to pretty-print draw_tree with indentation."""
        s = '\n%s%s,%s %s' % (tab, self.x, self.y, self.node.region)
        for quad in range(len(self.children)):
            if self.children[quad] is not None:
                s += self.children[quad].indent(tab + '  ')
        return s

    def __str__(self):
        """Return string representation of tree for debugging."""
        return self.indent('')
