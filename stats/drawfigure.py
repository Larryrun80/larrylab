#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Filename: drawfigure.py

import os

from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt
import pylab
import numpy as np


def init_figure():
    pylab.mpl.rcParams['font.sans-serif'] = ['Adobe Heiti Std']
    figure = plt.figure(figsize=(12, 5))
    font = FontProperties()

    font_title = font.copy()
    font_title.set_size('x-large')
    font_title.set_weight('bold')

    font_axis = font.copy()
    font_axis.set_size('medium')
    font_axis.set_weight('normal')
    font_axis.set_style('italic')

    # font_ticks = font.copy()
    # font_ticks.set_size('x-small')

    # figure.suptitle(title, fontproperties=font_title)

    # Tweak spacing to prevent clipping of tick-labels
    figure.subplots_adjust(bottom=0.2)

    ax = figure.add_subplot(111)
    ax.grid(True)
    ax.set_title('', fontproperties=font_axis)
    ax.set_xlabel('', fontproperties=font_axis)
    ax.set_ylabel('', fontproperties=font_axis)

    ax.tick_params(axis='both', which='major', labelsize='x-small')

    return figure, ax


def draw_line_chart(figure_type, save_path, x_data, y_data, x_ticks, **kwargs):
    FIGURE_TYPES = ('month', 'week')
    LINE_COLORS = ('orange', 'purple', 'blue', 'red', 'green',
                   'pink', 'yellow', 'grey', 'black')

    if figure_type not in FIGURE_TYPES:
        raise RuntimeError('illegal figure type found')
    if not os.path.exists(os.path.split(os.path.realpath(save_path))[0]):
        raise RuntimeError('dir for save figure is not exists')
    data_length = len(x_data)
    if len(x_ticks) != data_length:
        raise RuntimeError('mismatching length of x_data and x_ticks')
    for y in y_data:
        if not isinstance(y, dict) or len(y['data']) != data_length:
            raise RuntimeError('illegal y data found')

    figure, ax = init_figure()
    y_max = max([max(y_info['data']) for y_info in y_data])
    y_max = round(y_max/100*1.2)*100
    legend_cols = len(y_data)
    figure, ax = draw_line_chart_axises(figure_type, y_max,
                                        x_data, x_ticks, **kwargs)
    for i, line_data in enumerate(y_data, 0):
        draw_line_chart_lines(ax, x_data,
                              line_data['data'],
                              color=LINE_COLORS[i],
                              label=line_data['label'],
                              legend_cols=legend_cols,
                              **kwargs)

    plt.savefig(save_path)
    return save_path


def draw_line_chart_axises(type, y_max, x_data, xticks, **kwargs):
    '''kwargs now support 'title' and 'ylabel' '''
    # start drawing
    figure, ax = init_figure()
    if 'title' in kwargs.keys():
        ax.set_title(kwargs['title'])
    # setting axises
    ax.set_xlabel('')
    ax.xaxis.set_ticks(np.arange(0, len(x_data), 1.0))
    ax.set_xticklabels(xticks, rotation=60,)
    if 'ylabel' in kwargs.keys():
        ax.set_ylabel(kwargs['ylabel'])
    ax.set_ylim(ymin=0, ymax=y_max)
    return figure, ax


def draw_line_chart_lines(ax, x_data, y_data, **kwargs):
    ''' kwargs now support color, label, show_legend
        legend_cols and show_annotate'''
    color = kwargs.get('color', 'black')
    label = kwargs.get('label', None)
    line = ax.plot(x_data, y_data, color=color, linewidth=1, label=label)
    if 'show_annotate' in kwargs.keys() and kwargs['show_annotate']:
        annotate_v_offset = max(ax.get_ylim())/80
        for i, j in zip(x_data, y_data):
            ax.annotate(str(j),
                        xy=(i, j),
                        xytext=(i, j+annotate_v_offset),
                        fontsize=6,
                        color=color,
                        horizontalalignment='center')
    if 'show_legend' in kwargs.keys() and kwargs['show_legend']:
        ncols = kwargs.get('legend_cols', 1)
        ax.legend(loc='upper center', framealpha=0.5, fontsize='small',
                  ncol=ncols)
    return line, ax


def get_anntotate_v_offset(ymax):
    return ymax/80
