# -*- coding: utf-8 -*-

from django.conf import settings

import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.textpath
import matplotlib.colors
import matplotlib.gridspec
import matplotlib.cm
import mpl_toolkits.axisartist as axisartist
from matplotlib.patches import Rectangle
import textwrap
import os.path

import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ndarray size changed")

import scipy.sparse

import tadeus.HiCMatrix as HiCMatrix
import tadeus.utilities

from intervaltree import IntervalTree, Interval
from importlib import reload

import textwrap
import copy


reload(sys)

DEFAULT_HICMATRIX_HEIGHT = 10
DEFAULT_BED_HEIGHT = 4
DEFAULT_BEDGRAPH_HEIGHT = 3
DEFAULT_BEDGRAPH_WITH_BORDERS_STYLE_MAX_NUMBER_OF_ENTRIES = 500
DEFAULT_DOMAIN_HEIGHT = 3
DEFAULT_XAXIS_HEIGHT = 1
DEFAULT_BED_ENTRY_HEIGHT = 0.25
DEFAULT_ARCS_HEIGHT = 3
DEFAULT_VIRTUAL4C_HEIGHT = 2

DEFAULT_TRACK_HEIGHT = 4  # in centimeters
DEFAULT_FIGURE_WIDTH = 35  # in centimeters
# proportion of width dedicated to (figure, legends)
DEFAULT_WIDTH_RATIOS = (0.82, 0.18)


DEFAULT_MARGINS = {'left': 0, 'right': 1, 'bottom': 0, 'top': 1}


DEFAULT_VLINE_WIDTH = 1
DEFAULT_VLINE_ALPHA = 0.5
DEFAULT_VLINE_COLOR = (0, 0, 0, 0.7)
HIGHLIGHT_VLINE_COLOR = (1, 0, 0)
DEFAULT_VLINE_LINE_STYLE =  'dashed'

from tadeus.defaults import DEFAULT_WIDTH_PROP

def cm2inch(*tupl):
    inch = 2.54
    if isinstance(tupl[0], tuple):
        return tuple(i / inch for i in tupl[0])

    else:
        return tuple(i / inch for i in tupl)

class PlotTracks(object):

    def __init__(self, plot, fig_width = DEFAULT_FIGURE_WIDTH, dpi = None):

        self.plot = plot
        self.fig_width = fig_width
        self.dpi = dpi
        self.title = plot.title
        self.width_ratios = DEFAULT_WIDTH_RATIOS
        self.margins = DEFAULT_MARGINS

    def get_tracks_height(self, start, end):

        return [ track.height for track in self.plot.tracks.order_by('no', 'id').all() if not track.draw_vlines_only()]

class TrackPlot(object):
   
    def __init__(self, model):
        self.model = model
        self.track_file = model.track_file
        self.bed_type = model.track_file.bed_sub_type

        self.bin_sizes = self.track_file.bin_sizes

        if self.bin_sizes is not None:
            self.bin_sizes =  [ int(bin_size) for bin_size in self.bin_sizes.split() ]
    

        if model.title:
            if self.track_file.file_type == self.track_file.FILE_TYPE_HIC:
                self.title = textwrap.fill(model.title, 35) 
            else:
                self.title = textwrap.fill(model.title, 25)  

        self.domains_file = model.domains_file 
        
        self.height = model.height

        self.inverted = model.inverted

        self.color = '#' + model.color
        self.edgecolor =  '#' + model.edgecolor
        self.colormap = model.colormap

        self.min_value = model.min_value
        self.max_value = model.max_value

        self.transform = model.transform

        self.bed_display = model.bed_display
        self.bed_style = model.bed_style

        self.cmap = matplotlib.cm.get_cmap(self.colormap)
        self.cmap.set_bad('white')

        self.labels = model.labels

        self.v4c_chromosome = model.chromosome
        self.start_coordinate = model.start_coordinate
        self.end_coordinate = model.end_coordinate 

        self.aggregate_function = model.get_aggregate_function()
        
        self.bedgraph_style = model.bedgraph_style
        self.bedgraph_display = model.bedgraph_display
        self.bedgraph_type = model.bedgraph_type

        self.alpha =  0.8
        self.fontsize = 8

        from tadeus.models import Plot

        try:
            self.plot = model.plot
        except Plot.DoesNotExist:
            self.plot = None


    def get_figure_width(self):
        return self.fig_width * (self.margins['right'] - self.margins['left']) * self.width_ratios[0]

    def plot_vlines(self, vlines, axis, color):
        ymin, ymax = axis.get_ylim()

        axis.vlines(vlines, ymin, ymax, linestyle=DEFAULT_VLINE_LINE_STYLE, 
                              zorder=10,
                              linewidth=DEFAULT_VLINE_WIDTH,
                              color=color, alpha= DEFAULT_VLINE_ALPHA)

    def draw_track(self, cols, chrom, start, end, interval_start, interval_end, name_filter, breakpoint = None, left_side = None , width_prop = None,  breakpoint_coordinates = None):
        self.dpi = 600
        if width_prop is None:
            width_prop = DEFAULT_WIDTH_PROP
        self.fig_width = DEFAULT_FIGURE_WIDTH / cols * width_prop / DEFAULT_WIDTH_PROP
        self.width_ratios = DEFAULT_WIDTH_RATIOS
        self.margins = DEFAULT_MARGINS
        self.interval_start = interval_start
        self.interval_end = interval_end
        self.name_filter = name_filter
        self.breakpoint = breakpoint
        self.left_side = left_side
        self.width_prop = width_prop
        self.breakpoint_coordinates = breakpoint_coordinates
        self.visualize_breakpoint = self.breakpoint_coordinates and \
                                                'left_start' in self.breakpoint_coordinates and \
                                                'right_start' in self.breakpoint_coordinates  

        width = self.get_figure_width()

        fig = plt.figure()

        grids = matplotlib.gridspec.GridSpec(1, 1)
        
        self.axis = axisartist.Subplot(fig, grids[0, 0])
        fig.add_subplot(self.axis)
        #self.axis.axis[:].set_visible(False)
       
    
        # to make the background transparent
 
        trackPlot = self.draw(chrom, start, end, width)

        if self.plot:
            vlines = self.plot.getVLineEntries(chrom ,start, end)
            self.plot_vlines(vlines, self.axis, DEFAULT_VLINE_COLOR)

        if  interval_start:
            self.plot_vlines([interval_start, interval_end], self.axis, HIGHLIGHT_VLINE_COLOR)

        fig.subplots_adjust(wspace=0, hspace=0.0,
                            left=DEFAULT_MARGINS['left'],
                            right=DEFAULT_MARGINS['right'],
                            bottom=DEFAULT_MARGINS['bottom'],
                            top=DEFAULT_MARGINS['top'])

        self.height = self.get_height()
        fig.set_size_inches(cm2inch(self.fig_width, self.height))

        if breakpoint and left_side and breakpoint.left_inverse:
            self.axis.invert_xaxis()

        if breakpoint and not left_side and breakpoint.right_inverse:
            self.axis.invert_xaxis()

        return fig


    def draw_title(self):
        return

        if self.label_axis:
            self.height = self.get_height()
            y = 1- 0.05 * 4 / self.height 
            self.label_axis.text(0, y, self.title, fontsize=8, transform=self.label_axis.transAxes, verticalalignment = 'top')


    def draw_colorbar(self, img = None):
        return

        self.label_axis.set_axis_off()

        height = self.get_height() 
        aspect =  height / DEFAULT_HICMATRIX_HEIGHT * 20

        self.cbar_ax = copy.copy(self.label_axis)
        self.label_axis.set_axis_off()
        self.label_axis = self.cbar_ax 

        ticks = None

        if not img:
            ticks = np.linspace(self.min_value, self.max_value, max(int(height / 1.5), 3))
            img = plt.imshow(np.array([[self.min_value, self.max_value]]), cmap=self.cmap)
            img.set_visible(False)
        
        if self.model.track_file.file_type == 'HI' and  self.transform and self.transform in ['log', 'log1p']:
            from matplotlib.ticker import LogFormatter
            formatter = LogFormatter(10, labelOnlyBase=False)
            cobar = plt.colorbar(img, format=formatter, ax=self.label_axis, fraction=0.95)
        else:
            cobar = plt.colorbar(img, ax=self.label_axis, fraction=0.95, aspect = aspect, ticks=ticks)

        
        cobar.solids.set_edgecolor("face")
        cobar.ax.set_ylabel(self.title)

        # adjust the labels of the colorbar
        labels = cobar.ax.get_yticklabels()
        ticks = cobar.ax.get_yticks()


        if 0 in ticks and ticks[0] == 0:
            # if the label is at the start of the colobar
            # move it above avoid being cut or overlapping with other track
            labels[0].set_verticalalignment('bottom')
        if -1 in ticks and ticks[-1] == 1:
            # if the label is at the end of the colobar
            # move it a bit inside to avoid overlapping
            # with other labels
            labels[-1].set_verticalalignment('top')
        cobar.ax.set_yticklabels(labels)

    def print_data_range(self):

        return

        if float(self.max_value) % 1 == 0:
            max_value_print = int(self.max_value)
        else:
            max_value_print = "{:.1f}".format(self.max_value)

        if float(self.min_value) % 1 == 0:
            min_value_print = int(self.min_value)
        else:
            min_value_print = "{:.1f}".format(self.min_value)

        self.axis.set_ylim(self.min_value, self.max_value)
        ydelta = self.max_value - self.min_value
        small_x = 0.005 * (end - start)

        if self.show_data_range:

            self.axis.text(
                start + small_x, 
                self.max_value - ydelta * 0.2, 
                "[{}-{}]".format(min_value_print, max_value_print),
                horizontalalignment = 'left', 
                fontsize = 8,
                verticalalignment = 'bottom'
            )


class PlotBed(TrackPlot):

    def __init__(self, *args, **kwarg):
        super(PlotBed, self).__init__(*args, **kwarg)

        self.interval_height = 10
        self.row_scale = self.interval_height * 2

    def get_height(self):
        if self.height is not None:
            return self.height

        if self.display == 'stacked':
            if self.max_num_row == 0: 
                return DEFAULT_BED_ENTRY_HEIGHT 
            return 2 * DEFAULT_BED_ENTRY_HEIGHT * self.max_num_row  - DEFAULT_BED_ENTRY_HEIGHT 
        elif self.display == 'interlaced':
            return 5 * DEFAULT_BED_ENTRY_HEIGHT 
        else:
            return 3 *  DEFAULT_BED_ENTRY_HEIGHT


    def get_y_pos(self, free_row):

        if self.display == 'interlaced':
            ypos = self.interval_height if self.counter % 2 == 0 else self.interval_height + self.row_scale 

        elif self.display == 'collapsed':
            ypos = self.interval_height 

        else:
            ypos = free_row * self.row_scale + self.interval_height 

        return ypos

    def get_max_y_pos(self):

        if self.display == 'interlaced':
            ypos = self.interval_height + 2 * self.row_scale
        elif self.display == 'collapsed':
            ypos = self.interval_height * 3 
        else:
            ypos = self.max_num_row * self.row_scale + self.interval_height 

        return ypos
 

    def has_colormap(self):
        return self.colormap  and self.min_value is not None and self.max_value is not None and self.min_value != self.max_value


    def set_colormap(self):
        
        if self.has_colormap():
            color_options = [m for m in matplotlib.cm.datad]
            norm = matplotlib.colors.Normalize(vmin=self.min_value,
                                               vmax=self.max_value)
            cmap = matplotlib.cm.get_cmap(self.colormap)
            self.colormap = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)


    def process_bed(self, fig_width, chrom, start, end):

        # to improve the visualization of the genes
        # it is good to have an estimation of the label
        # length. In the following code I try to get
        # the length of a 'W'.
        
        if self.labels:
            # from http://scipy-cookbook.readthedocs.org/items/Matplotlib_LaTeX_Examples.html
            inches_per_pt = 1.0 / 72.27
            font_in_inches = self.fontsize * inches_per_pt
            region_len = end - start
            bp_per_inch = region_len / fig_width
            font_in_bp = font_in_inches * bp_per_inch
            self.len_w = font_in_bp
            print("len of w set to: {} bp".format(self.len_w))
        else:
            self.len_w = 1

        self.interval_tree = IntervalTree()


        # check for the number of other intervals that overlap
        #    with the given interval
        #            1         2
        #  012345678901234567890123456
        #  1=========       4=========
        #       2=========
        #         3============
        #
        # for 1 row_last_position = [9]
        # for 2 row_last_position = [9, 14]
        # for 3 row_last_position = [9, 14, 19]
        # for 4 row_last_position = [26, 14, 19]

        row_last_position = []  # each entry in this list contains the end position
        # of genomic interval. The list index is the row
        # in which the genomic interval was plotted.
        # Any new genomic interval that wants to be plotted,
        # knows the row to use by finding the list index that
        # is larger than its start

        max_score = None
        min_score = None

        entries = self.model.get_entries(chrom, start, end, self.name_filter)

        if len(entries) > 60:
            self.labels = False

        for entry in entries:
     
            # check for overlapping genes including
            # label size (if plotted

            if self.labels and entry.name is not None:
                entry_extended_end = int(entry.end + (len(entry.name) * self.len_w))
            else:
                entry_extended_end = (entry.end + 2 * self.small_relative)

            # get smallest free row
            if len(row_last_position) == 0:
                free_row = 0
                row_last_position.append(entry_extended_end)
            else:
                # get list of rows that are less than bed.start, then take the min
                idx_list = [idx for idx, value in enumerate(row_last_position) if value < entry.start]
                if len(idx_list):
                    free_row = min(idx_list)
                    row_last_position[free_row] = entry_extended_end
                else:
                    free_row = len(row_last_position)
                    row_last_position.append(entry_extended_end)

            self.interval_tree.add(Interval(entry.start, entry.end, (entry, free_row)))

            if entry.score is not None:
                max_score = entry.score if max_score is None else max(entry.score, max_score)
                min_score = entry.score if min_score is None else min(entry.score, min_score)

        """
        if self.min_value is None:
            self.min_value = min_score
 
        if self.max_value is None:
            self.max_value = max_score           
        """

        self.max_num_row = len(row_last_position)

        self.set_colormap()

    def draw(self,  chrom, start, end, width):

        self.counter = 0
        self.small_relative = 0.004 * (end - start)

        self.process_bed(self.axis.get_figure().get_figwidth(), chrom, start, end)

        
        for region in self.interval_tree:
            """
            BED12 gene format with exon locations at the end
            chrX    20850   23076   CG17636-RA      0       -       20850   23017   0       3       946,765,64,     0,1031,2162,

            BED9
            bed with rbg at end
            chr2L   0       70000   ID_5    0.26864549832   .       0       70000   51,160,44

            BED6
            bed with rbg at end
            chr2L   0       70000   ID_5    0.26864549832   .
            """
    
            entry, free_row = region.data
                     
            edgecolor = self.edgecolor

            if entry.itemRGB is not None:
                rgb = '#' + entry.itemRGB
            elif entry.score is not None and self.has_colormap():
                rgb = self.colormap.to_rgba(entry.score)
                edgecolor = self.colormap.to_rgba(float(entry.score))
            else:
                rgb = 'black'

            ypos = self.get_y_pos(free_row)

            if self.track_file.bed_sub_type == self.track_file.BED12 and self.bed_display == self.BED_DISPLAY_FLYBASE:
                self.draw_gene_with_introns_flybase_style(entry, ypos, rgb = rgb, edgecolor = edgecolor)
            elif self.track_file.bed_sub_type == self.track_file.BED12 and self.bed_display == self.BED_DISPLAY_INTRONS:
                self.draw_gene_with_introns(entry, ypos, rgb = rgb, edgecolor = edgecolor)
            else:
                self.draw_gene_simple(entry, ypos, rgb = rgb, edgecolor = edgecolor)

            if self.labels and entry.start > start and entry.end < end  and entry.name is not None:
                self.axis.text(entry.end + self.small_relative, ypos + (float(self.interval_height) / 2),
                        entry.name, horizontalalignment='left',
                        verticalalignment='center')

            self.counter += 1

        ymax = 0
        ymin = self.get_max_y_pos()

        self.axis.set_ylim(ymin, ymax)
        self.axis.set_xlim(start, end)

        if self.has_colormap():
            self.draw_colorbar()
        else:        
            self.draw_title()

    def draw_gene_simple(self, entry, ypos, rgb, edgecolor):
        """
        draws an interval with direction (if given)
        """
        from matplotlib.patches import Polygon

        if entry.strand not in ['+', '-']:
            self.axis.add_patch(Rectangle((entry.start, ypos), entry.end - entry.start, self.interval_height,
                                 edgecolor=edgecolor, facecolor=rgb, 
                                 linewidth=0.5))
        else:
            vertices = self._draw_arrow(entry.start, entry.end, entry.strand, ypos)
            self.axis.add_patch(Polygon(vertices, closed=True, fill=True,
                                 edgecolor=edgecolor,
                                 facecolor=rgb,
                                 linewidth=0.5))

    def draw_gene_with_introns_flybase_style(self, entry, ypos, rgb, edgecolor):
        """
        draws a gene using different styles
        """
        from matplotlib.patches import Polygon
        if entry.block_count == 0 and entry.thick_start == entry.start and entry.thick_end == entry.end:
            self.draw_gene_simple(self.axis, entry, ypos, rgb, edgecolor)
            return
        half_height = float(self.interval_height) / 2
        # draw 'backbone', a line from the start until the end of the gene
        self.axis.plot([entry.start, entry.end], [ypos + half_height, ypos + half_height], 'black', linewidth=0.5, zorder=-1)

        # get start, end of all the blocks
        positions = []
        block_starts = entry.get_block_starts()
        block_sizes = entry.get_block_sizes()
        carol_t = self.carol(entry.name)

        for idx in range(0, entry.block_count):

            x0 = entry.start + block_starts[idx]
            x1 = x0 +  block_sizes[idx]
            if x0 < entry.thick_start < x1:
                positions.append((x0, entry.thick_start, 'UTR' , carol_t[idx]))
                positions.append((entry.thick_start, x1, 'coding', carol_t[idx]))

            elif x0 < entry.thick_end < x1:
                positions.append((x0, entry.thick_end, 'coding', carol_t[idx]))
                positions.append((entry.thick_end, x1, 'UTR', carol_t[idx]))

            else:
                if x1 < entry.thick_start or x0 > entry.thick_end:
                    type = 'UTR'
                else:
                    type = 'coding'

                positions.append((x0, x1, type, carol_t[idx]))

        if  not carol_t:
            # plot all blocks as rectangles except the last if the strand is + or
            # the first is the strand is -, which are drawn as arrows
            if entry.strand == '-':
                positions = positions[::-1]

            first_pos = positions.pop()

            """
            if first_pos[2] == 'UTR':
                _rgb = 'grey'
            else:"""
            _rgb = rgb

            vertices = self._draw_arrow(first_pos[0], first_pos[1], entry.strand, ypos)

            self.axis.add_patch(Polygon(vertices, closed=True, fill=True,
                                 edgecolor=edgecolor,
                                 facecolor='green',
                                 linewidth=0.5))

    
        for start_pos, end_pos, _type, carol in positions:
            """if _type == 'UTR':
                _rgb = 'grey'
            else:"""
            _rgb = rgb
            vertices = [(start_pos, ypos), (start_pos, ypos + self.interval_height),
                        (end_pos, ypos + self.interval_height), (end_pos, ypos)]

            if carol_t:
                _rgb = 'blue' if carol else 'red'

            self.axis.add_patch(Polygon(vertices, closed=True, fill=True,
                                 edgecolor= edgecolor,
                                 facecolor=_rgb,
                                 linewidth=0.5))

    def _draw_arrow(self, start, end, strand, ypos):
        """
        Draws a filled arrow
        :param ax:
        :param start:
        :param end:
        :param strand:
        :param ypos:
        :param rgb:
        :return: None
        """

        x0 = start
        x1 = end  # - self.small_relative
        y0 = ypos
        y1 = ypos + self.interval_height

        half_height = float(self.interval_height) / 2
        if strand == '+':
       
            """
            The vertices correspond to 5 points along the path of a form like the following,
            starting in the lower left corner and progressing in a clock wise manner.

            -----------------\
            ---------------- /

            """

            vertices = [(x0, y0), (x0, y1), (x1, y1), (x1 + self.small_relative, y0 + half_height), (x1, y0)]
        else:
            """
            The vertices correspond to 5 points along the path of a form like the following,
            starting in the lower left corner and progressing in a clock wise manner.

            /-----------------
            \-----------------
            """
            vertices = [(x0, y0), (x0 - self.small_relative, y0 + half_height), (x0, y1), (x1, y1), (x1, y0)]

        return vertices

    def draw_gene_with_introns(self, entry, ypos, rgb, edgecolor):
        """
        draws a gene like in flybase gbrowse.
        """
        from matplotlib.patches import Polygon

        if entry.block_count == 0 and entry.thick_start == entry.start and entry.thick_end == entry.end:
            self.draw_gene_simple(entry, ypos, rgb, edgecolor)
            return
        half_height = float(self.interval_height) / 2
        quarter_height = float(self.interval_height) / 4
        three_quarter_height = quarter_height * 3

        # draw 'backbone', a line from the start until the end of the gene
        self.axis.plot([entry.start, entry.end], [ypos + half_height, ypos + half_height], 'black', linewidth=0.5, zorder=-1)

        block_starts = entry.get_block_starts()
        block_sizes = entry.get_block_sizes()

        for idx in range(0, entry.block_count):
            x0 = entry.start + block_starts[idx]
            x1 = x0 + block_sizes[idx]
            if x1 < entry.thick_start or x0 > entry.thick_end:
                y0 = ypos + quarter_height
                y1 = ypos + three_quarter_height
            else:
                y0 = ypos
                y1 = ypos + self.interval_height

            if x0 < entry.thick_start < x1:
                vertices = ([(x0, ypos + quarter_height), (x0, ypos + three_quarter_height),
                             (entry.thick_start, ypos + three_quarter_height),
                             (entry.thick_start, ypos + self.interval_height),
                             (entry.thick_start, ypos + self.interval_height),
                             (x1, ypos + self.interval_height), (x1, ypos),
                             (entry.thick_start, ypos), (entry.thick_start, ypos + quarter_height)])

            elif x0 < entry.thick_end < x1:
                vertices = ([(x0, ypos),
                             (x0, ypos + self.interval_height),
                             (entry.thick_end, ypos + self.interval_height),
                             (entry.thick_end, ypos + three_quarter_height),
                             (x1, ypos + three_quarter_height),
                             (x1, ypos + quarter_height),
                             (entry.thick_end, ypos + quarter_height),
                             (entry.thick_end, ypos)])
            else:
                vertices = ([(x0, y0), (x0, y1), (x1, y1), (x1, y0)])

            self.axis.add_patch(Polygon(vertices, closed=True, fill=True,
                                 linewidth=0.1,
                                 edgecolor='none',
                                 facecolor=rgb))

            if idx < entry.block_count - 1:
                # plot small arrows using the character '<' or '>' over the back bone
                intron_length = block_starts[idx + 1] - (block_starts[idx] + block_sizes[idx])
                marker = 5 if entry.strand == '+' else 4
                if intron_length > 3 * self.small_relative:
                    pos = np.arange(x1 + 1 * self.small_relative,
                                    x1 + intron_length + self.small_relative, int(2 * self.small_relative))
                    self.axis.plot(pos, np.zeros(len(pos)) + ypos + half_height, '.', marker=marker,
                            fillstyle='none', color=self.color, markersize=3)

                elif intron_length > self.small_relative:
                    intron_center = x1 + int(intron_length) / 2
                    self.axis.plot([intron_center], [ypos + half_height], '.', marker=5,
                            fillstyle='none', color=self.color, markersize=3)




class PlotXAxis(TrackPlot):

    def __init__(self, *args, **kwargs):
        super(PlotXAxis, self).__init__(*args, **kwargs)

    def get_height(self):
        return self.height if self.height is not None else DEFAULT_XAXIS_HEIGHT


    def draw(self, chrom, start, end, width):
        self.axis.axis['x'] = self.axis.new_floating_axis(0, 0.5)

        size = end - start

        if size <= 4e3:
            scale = 1
            text = ''    
        elif size <= 1e6:
            scale = 1e3
            text = 'Kbp'
        else:
            scale = 1e6
            text = 'Mbp'

        scaled_start= start/scale
        scaled_end =end/scale

        self.axis.set_xlim(scaled_start, scaled_end)

        self.axis.text(scaled_end, 0.575, text,   verticalalignment='bottom', horizontalalignment='right', fontsize = self.fontsize)

        self.axis.axis['x'].major_ticklabels.set(size=self.fontsize)
        
        self.axis.axis['x'].set_axis_direction('top')

class PlotBedGraph(TrackPlot):

    def __init__(self, *args, **kwargs):
        super(PlotBedGraph, self).__init__(*args, **kwargs)

    def get_height(self):
        return self.height if self.height is not None else DEFAULT_BEDGRAPH_HEIGHT

    def stack_entries(self):
        no_of_layers = len(self.entries_list)
        no_of_bins = len(self.entries_list[0])

        for i in range(no_of_layers - 1):
            for j in range(no_of_bins):
                self.entries_list[no_of_layers - i - 2][j].score += self.entries_list[no_of_layers - i - 1][j].score

    def draw(self, chrom, start, end, width):

        self.draw_title()

        self.axis.set_frame_on(False)
        self.axis.axes.get_xaxis().set_visible(False)

        self.entries_list = self.model.get_entries(chrom, start, end)

        if self.bedgraph_display == self.model.BEDGRAPH_DISPLAY_STACKED:
            self.stack_entries()

        interpolate = True
        alpha = 1

        if self.bedgraph_display == self.model.BEDGRAPH_DISPLAY_TRANSPARENT:
            interpolate = False
            alpha = 0.4

        min_value = self.entries_list[0][0].score
        max_value = self.entries_list[0][0].score            

        for entries, subtrack in zip(self.entries_list, self.model.subtracks.all()):

            score_list = []
            pos_list = []

            for entry in entries:
                if entry.score is not  None:

                    if self.bedgraph_type == self.model.BEDGRAPH_TYPE_LINECHART:
                        score_list.append(entry.score)
                        pos_list.append(entry.start + (entry.end - entry.start) / 2)
                    else:
                        score_list += [entry.score, entry.score]
                        pos_list += [entry.start, entry.end ]

                    max_value = max(max_value, entry.score)
                    min_value = min(min_value, entry.score)

            if len(score_list) == 0:
                continue            
               
            color = subtrack.rgb 
            egde_color = self.edgecolor

            if self.bedgraph_style == self.model.BEDGRAPH_STYLE_LINE:
                self.axis.plot(pos_list, score_list, '-', color = color, linewidth = 0.7)
            else:
                self.axis.fill_between(pos_list, score_list, interpolate = interpolate, alpha = alpha, facecolor = color, edgecolor = 'none')

        if self.max_value is None:
            self.max_value = max_value

        if self.min_value is None:
            self.min_value = min_value

        self.print_data_range()    
        self.axis.set_xlim(start, end)
 
class PlotDomains(TrackPlot):

    def __init__(self, *args, **kwargs):
        super(PlotDomains, self).__init__(*args, **kwargs)


    def get_height(self):
        return self.height if self.height is not None else DEFAULT_DOMAIN_HEIGHT

    def draw(self, chrom, start, end, width):
        """
        Plots the boundaries as triangles in the given ax.
        """
        x = []
        y = []

        for entry in self.model.get_entries(chrom, start, end):
            """
                  /\
                 /  \
                /    \
            _____________________
               x1 x2 x3
            """
            x1 = entry.start
            x2 = x1 + float(entry.end - entry.start) / 2
            x3 = entry.end
            y1 = 0
            y2 = (entry.end - entry.start)
            x.extend([x1, x2, x3])
            y.extend([y1, y2, y1])

        self.axis.plot(x, y, color = self.color)
        self.axis.set_xlim(start, end)

        self.draw_title()


class PlotArcs(TrackPlot):

    def __init__(self, *args, **kwarg):
        super(PlotArcs, self).__init__(*args, **kwarg)

    def get_height(self):
        return self.height if self.height is not None else DEFAULT_ARCS_HEIGHT


    def draw(self, chrom, start, end, width):
        """
        Makes and arc connecting two points on a linear scale representing
        interactions between Hi-C bins.
        :param ax: matplotlib axis
        :param label_ax: matplotlib axis for labels
        """
        from matplotlib.patches import Arc

        max_diameter = 0

        for idx, interval in enumerate(self.model.get_entries(chrom, start, end, self.name_filter)): #enumerate(self.model.get_entries(chrom, self.interval_start, self.interval_start)):

            diameter = interval.end - interval.start
            center = interval.start + float(diameter) / 2

            if diameter > max_diameter:
                max_diameter = diameter

            self.axis.plot([center], [diameter])

            line_width = 0.5 * np.sqrt(float(abs(interval.score)))

            self.axis.add_patch(Arc((center, 0), diameter,
                             diameter * 2, 0, 0, 180, color=self.color, lw=line_width))

        if self.inverted:
            self.axis.set_ylim(max_diameter, -1)
        else:
            self.axis.set_ylim(-1, max_diameter)

        self.axis.set_xlim(start, end)

        self.draw_title()

class PlotHiCMatrix(TrackPlot):

    def __init__(self, *args, **kwarg):
        super(PlotHiCMatrix, self).__init__(*args, **kwarg)

        self.show_masked_bins = False        

        """
        if  self.show_masked_bins:
            pass
        else:
            self.hic_ma.maskBins(self.hic_ma.nan_bins)
        """
   
        """"
        new_intervals = tadeus.utilities.enlarge_bins(self.hic_ma.cut_intervals)
        self.hic_ma.interval_trees, self.hic_ma.chrBinBoundaries = \
            self.hic_ma.intervalListToIntervalTree(new_intervals)


        self.hic_ma.cut_intervals = new_intervals
        binsize = self.hic_ma.getBinSize()
        max_depth_in_bins = int(self.depth / binsize)
        """

        # work only with the lower matrix
        # and remove all pixels that are beyond
        # 2 * max_depth_in_bis which are not required
        # (this is done by subtracting a second sparse matrix
        # that contains only the lower matrix that wants to be removed.

        """
        limit = 2 * max_depth_in_bins
        self.hic_ma.matrix = scipy.sparse.triu(self.hic_ma.matrix, k=0, format='csr') - \
            scipy.sparse.triu(self.hic_ma.matrix, k=limit, format='csr')
        self.hic_ma.matrix.eliminate_zeros()
        """

        # fill the main diagonal, otherwise it looks
        # not so good. The main diagonal is filled
        # with an array containing the max value found
        # in the matrix
        
        """"
        if sum(self.hic_ma.matrix.diagonal()) == 0:
            sys.stderr.write("Filling main diagonal with max value "
                             "because it empty and looks bad...\n")
            max_value = self.hic_ma.matrix.data.max()

            main_diagonal = scipy.sparse.dia_matrix(([max_value] * self.hic_ma.matrix.shape[0], [0]),
                                                    shape=self.hic_ma.matrix.shape)
            self.hic_ma.matrix = self.hic_ma.matrix + main_diagonal
        """

        self.norm = None

        self.height = self.get_height()

    def get_height(self):
        return self.height if self.height is not None else DEFAULT_HICMATRIX_HEIGHT

    def draw(self, chrom, start, end, width):

        self.chrom_size = self.track_file.assembly.chromosomes.get(name = chrom).size

        plot_width = width * DEFAULT_WIDTH_RATIOS[0]
        region_len = end - start
        bp_in_cm  = region_len // plot_width

        stat = [  (abs( 15 - bp_in_cm   / bin_size / 1000), bin_size) for bin_size in self.bin_sizes]
        stat.sort(key =  lambda x : x[0])

        self.resolution = 10  #stat[0][1]
        self.bin_size = self.resolution  * 1000

        self.hic_ma = HiCMatrix.hiCMatrix(settings.PROJECT_DATA_ROOT.format(resolution = self.resolution ) 
         + '/' + self.file_path.format(resolution = self.resolution ))

        depth =  self.height / width * region_len / 0.51

        depth_in_bins = int(region_len / self.bin_size)

        matrix_start = max(start - depth, 0)
        matrix_end = min(end + depth, self.chrom_size - self.bin_size)

        matrix = self.hic_ma.get_sub_matrix(chrom, matrix_start, matrix_end)
        start_pos = self.hic_ma.get_start_pos(chrom, matrix_start, matrix_end + self.bin_size)
    
        if self.transform:
            if self.transform == 'log1p':
                matrix += 1
                self.norm = matplotlib.colors.LogNorm()

            elif self.transform == '-log':
                mask = matrix == 0
                matrix[mask] = matrix[mask is False].min()
                matrix = -1 * np.log(matrix)

            elif self.transform == 'log':
                mask = matrix == 0
                matrix[mask] = matrix[mask is False].min()
                matrix = np.log(matrix)

        if not self.max_value is None:
            vmax = self.max_value
            print('vmax:', vmax)
        else:    
            # try to use a 'aesthetically pleasant' max value
            vmax = np.nanpercentile(matrix.diagonal(1), 80) #nanpercentile

        if not self.min_value is None:
            vmin = self.min_value
            print('vmin', vmin)
        else:
            # if the region length is large with respect to the chromosome length, the diagonal may have
            # very few values or none. Thus, the following lines reduce the number of bins until the
            # diagonal is at least length 5
            distant_diagonal_values = [1]
            num_bins_from_diagonal = depth_in_bins

            for num_bins in reversed(range(num_bins_from_diagonal)):
                distant_diagonal_values = matrix.diagonal(num_bins)
                if len(distant_diagonal_values) > 5:
                    break

            vmin = np.nanmedian(distant_diagonal_values)

        #img = self.pcolormesh_45deg(matrix, start_pos, vmax=vmax, vmin= vmin)

        img = self.pcolormesh_45deg(matrix, start_pos, vmax=vmax, vmin= vmin)
        img.set_rasterized(True)

        if self.inverted:
            self.axis.set_ylim(depth, 0)
        else:
            self.axis.set_ylim(0, depth)

        if self.domains_file:   
            from tadeus.models import Track
            track = Track(track_file = self.domains_file)
            track.color = 'FF0000'
            trackPlot  = PlotDomains(model = track)
            trackPlot.axis = self.axis
            trackPlot.label_axis = None
            trackPlot.draw(chrom, start, end, width)
        
        self.axis.set_xlim(start, end)

        self.draw_colorbar(img = img)

    def bin_adjust(self, n, bin_size):

        return n // bin_size * bin_size

##########################################################################################################
##########################################################################################################

    def get_sub_matrix(self, chrom_name, adj_start, adj_end, bin_size):
        

        adj_size = adj_end - adj_start
        no_bins = adj_size // bin_size

        matrix = np.empty((no_bins, no_bins,))
        matrix[:] = np.nan

        adj_hic_start = max(adj_start, 0)
        adj_hic_end = adj_end #min(adj_end, adj_chrom_size)

        diff_bins_start = (adj_hic_start - adj_start) // bin_size
        diff_bins_end = (adj_end - adj_hic_end) // bin_size

        submatrix  = self.hic_ma.get_sub_matrix(chrom_name, adj_hic_start, adj_hic_end)
 
        matrix[diff_bins_start:no_bins - diff_bins_end, diff_bins_start:no_bins - diff_bins_end] = submatrix

        return matrix

    def get_chromosome_size(self, chrom_name):
        return self.hic_ma.get_chromosome_size(chrom_name)


    def get_sub_matrix(self, bin_size,  chrom_name1, adj_start1, adj_end1, chrom_name2 = None, adj_start2 = None, adj_end2 = None):

        def get_range(chrom_name, adj_start, adj_end):
        
            adj_size = adj_end - adj_start
            no_bins = adj_size // bin_size

            adj_hic_start = max(adj_start, 0)
            chrom_size = self.get_chromosome_size(chrom_name)
            adj_hic_end = min(adj_end, self.bin_adjust(chrom_size, bin_size))

            diff_bins_start = (adj_hic_start - adj_start) // bin_size
            diff_bins_end = (adj_end - adj_hic_end) // bin_size

            return  no_bins, adj_hic_start, adj_hic_end, diff_bins_start, no_bins - diff_bins_end

        if chrom_name2 is None:
            chrom_name2  = chrom_name1
            adj_start2 = adj_start1
            adj_end2 = adj_end1    

        no_bins1, adj_hic_start1, adj_hic_end1, diff_bins_start1, diff_bins_end1 = get_range(chrom_name1, adj_start1, adj_end1)
        no_bins2, adj_hic_start2, adj_hic_end2, diff_bins_start2, diff_bins_end2 = get_range(chrom_name2, adj_start2, adj_end2)

        matrix = np.empty((no_bins1, no_bins2,))
        matrix[:] = np.nan

        submatrix = self.hic_ma.get_sub_matrix(chrom_name1, adj_hic_start1, adj_hic_end1, chrom_name2, adj_hic_start2, adj_hic_end2)
 
        matrix[diff_bins_start1:diff_bins_end1, diff_bins_start2:diff_bins_end2] = submatrix

        return matrix


    def get_breakpoint_matrix(self, bin_size, adj_depth):

        left_inverse = self.breakpoint.left_inverse
        right_inverse = self.breakpoint.right_inverse

        left_start = self.breakpoint_coordinates['left_start']
        left_end = self.breakpoint_coordinates['left_end']

        right_start = self.breakpoint_coordinates['right_start']
        right_end = self.breakpoint_coordinates['right_end']

        print(left_start, left_end, right_start, right_end)

        if not self.breakpoint.left_inverse:
            left_start_adj = self.bin_adjust(left_start, bin_size) - adj_depth 
            left_end_adj = self.bin_adjust(left_end + bin_size // 2, bin_size)  
        else:
            left_start_adj = self.bin_adjust(left_start, bin_size) - adj_depth 
            left_end_adj = self.bin_adjust(left_end + bin_size // 2, bin_size)  + adj_depth
 
        if not self.breakpoint.right_inverse:                
            right_start_adj = self.bin_adjust(right_start + bin_size // 2, bin_size)
            right_end_adj = self.bin_adjust(right_end + bin_size, bin_size)  + adj_depth
        else:
            right_start_adj = self.bin_adjust(right_start + bin_size // 2, bin_size) - adj_depth
            right_end_adj = self.bin_adjust(right_end + bin_size, bin_size)

        left_no_bins = (left_end_adj - left_start_adj) // bin_size
        right_no_bins = (right_end_adj - right_start_adj) // bin_size 
        no_bins = left_no_bins + right_no_bins 

        if not self.breakpoint.left_inverse:
            left_br_start = left_start_adj
        else:
            left_br_start = left_end_adj - no_bins * bin_size

        if not self.breakpoint.right_inverse:
            right_br_start = right_start_adj - left_no_bins * bin_size 
        else:
            right_br_start = left_end_adj - right_no_bins * bin_size  

        matrix = np.empty((no_bins,no_bins,))

        matrix[:] = np.nan

        matrix = self.get_sub_matrix(bin_size, self.breakpoint.left_chrom.name, left_br_start, left_br_start +  no_bins * bin_size, 
                                     self.breakpoint.right_chrom.name, right_br_start, right_br_start +  no_bins * bin_size)

        if left_inverse:
            matrix = np.flipud(matrix)

        if right_inverse:
            matrix = np.fliplr(matrix)

        matrix_size = matrix.shape[0] 

        left_matrix = self.get_sub_matrix(bin_size, self.breakpoint.left_chrom.name, left_start_adj, left_end_adj)

        if left_inverse:
            left_matrix = np.flipud(left_matrix)
            left_matrix = np.fliplr(left_matrix)

        left_matrix_size = left_matrix.shape[0]
        #matrix[0:left_matrix_size,0:left_matrix_size] = left_matrix
        
        right_matrix = self.get_sub_matrix(bin_size, self.breakpoint.right_chrom.name, right_start_adj, right_end_adj)
        
        if right_inverse:
            right_matrix = np.flipud(right_matrix)
            right_matrix = np.fliplr(right_matrix)

        right_matrix_size = right_matrix.shape[0] 
        #matrix[matrix_size - right_matrix_size:matrix_size, matrix_size - right_matrix_size:matrix_size] = right_matrix

        if self.left_side:
            start_matrix = left_start_adj
        else:
            start_matrix = right_start_adj - left_no_bins * bin_size

        print(no_bins, left_start_adj, left_end_adj, left_no_bins, right_start_adj, right_end_adj, right_no_bins, start_matrix)
        print(matrix_size, left_matrix_size, right_matrix_size)

        return matrix, start_matrix


    def draw(self, chrom, start, end, width):

        self.resolution = 1

        self.hic_ma = HiCMatrix.hiCMatrix('/home/basia/CNVBrowser/tadeus2/4DNFI18UHVRO.mcool::resolutions/50000')

        bin_size = 50 * 1000
        depth =   2000 * 1000

        adj_depth = self.bin_adjust(depth, bin_size)
       
        if self.visualize_breakpoint:
            
            matrix, start_matrix = self.get_breakpoint_matrix(bin_size, adj_depth)
            no_bins = np.shape(matrix)[0]
            
        else:
            
            adj_start = self.bin_adjust(start, bin_size)
            adj_end = self.bin_adjust(end, bin_size) 
            adj_size = adj_end - adj_start

            no_bins = int((adj_size + 2 * adj_depth) // bin_size)
            start_matrix = adj_start - adj_depth
            end_matrix =  adj_start + adj_depth + adj_size 

            matrix = self.get_sub_matrix(chrom, start_matrix, end_matrix, bin_size )

        start_pos =  list(range(start_matrix, start_matrix + bin_size * (no_bins + 1), bin_size))

        matrix += 1
        self.norm = matplotlib.colors.LogNorm()

        img = self.pcolormesh_45deg(matrix, start_pos, vmax=50, vmin= 1)
        img.set_rasterized(True)

        print(start, end)
        self.axis.set_xlim(start, end)
        #self.axis.set_xlim(start_pos[0], start_pos[-1])
        self.axis.set_ylim(- adj_depth, adj_depth)

        self.draw_colorbar(img = img)

    def pcolormesh_45deg(self, matrix_c, start_pos_vector, vmin=None,
                         vmax=None):
        """
        Turns the matrix 45 degrees and adjusts the
        bins to match the actual start end positions.
        """
        import itertools

        # code for rotating the image 45 degrees
        n = matrix_c.shape[0]
        # create rotation/scaling matrix
        t = np.array([[1, 0.5], [-1, 0.5]])
        # create coordinate matrix and transform it

        matrix_a = np.dot(np.array([(i[1], i[0])
                                    for i in itertools.product(start_pos_vector[::-1],
                                                               start_pos_vector)]), t)

        # this is to convert the indices into bp ranges
        x = matrix_a[:, 1].reshape(n + 1, n + 1)
        y = matrix_a[:, 0].reshape(n + 1, n + 1)

        #print(x)
        #print(y)

        # plot

        im = self.axis.pcolormesh(x, y, np.flipud(matrix_c),
                                vmin=vmin, vmax=vmax, cmap=self.cmap, norm=self.norm)
        return im

class PlotVirtualHIC(TrackPlot):

    def __init__(self, *args, **kwarg):
        super(PlotVirtualHIC, self).__init__(*args, **kwarg)
        self.hic_ma = HiCMatrix.hiCMatrix('/home/basia/CNVBrowser/tadeus/4DNFIQI8SFNE.mcool::resolutions/50000')
        self.bin_size = 50 * 1000

    def aggregate_and_transform(self, columns):
        agg = np.apply_along_axis(self.aggregate_function, 0, columns)
        return agg


    def draw(self, chrom, start, end, width):
        print(self.v4c_chromosome, self.start_coordinate, self.end_coordinate)
        
        all_columns = self.hic_ma.get_column_region(self.v4c_chromosome.name, self.start_coordinate, self.end_coordinate, chrom)
        columns = self.hic_ma.get_sub_matrix(self.v4c_chromosome.name, self.start_coordinate, self.end_coordinate, chrom, start, end)


        all_values =  self.aggregate_and_transform(all_columns)
        values =  self.aggregate_and_transform(columns)

        start_positions =  list(self.hic_ma.get_start_positions(chrom, start, end))
        
        for start_position, value in zip(start_positions, values):
            self.axis.add_patch(Rectangle((start_position, 0), self.bin_size, value, edgecolor=self.edgecolor, linewidth = 1))

        max_value = np.max(values)

        #self.axis.set_ylim(-max_value * 0.05, max_value * 1.05)
        self.axis.set_ylim(-max_value * 0.05, 40)
        self.axis.set_xlim(start, end)


    def get_height(self):
        return self.height if self.height is not None else DEFAULT_VIRTUAL4C_HEIGHT