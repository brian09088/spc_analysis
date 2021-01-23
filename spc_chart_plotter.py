# -*- coding: utf-8 -*-
"""
Created on 2020/12/19 下午 01:26
@author: Ivan Y.W.Chiu
"""

import pandas as pd
import numpy as np
import os, sys, time, random
from datetime import datetime
from spc_data_generator import SPCDataConfig, SPCDataGenerator
import matplotlib as mpl
# matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle as RT
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

line_color = [46/255, 117/255, 182/255]

# %%
################################
# Generate demo SPC data
################################
mpl.rcParams.update({"font.size": "8",
                     'lines.linewidth': 1,
                     'lines.markersize': 4})
data_cnt = 300
process_name = 'PROC-001-2'
chart_name = 'WEIGHT'
chart_type = 'MEAN'
chart_descpt = 'A demo SPC chart'

spc_cfg = SPCDataConfig('2020/11/17 00:00:00.0', '2020/12/18 00:00:00.0', ctype=chart_type, cnt=data_cnt, data_order=0.1, sl=0.3, cl=0.2, target=0)
SPC = SPCDataGenerator(spc_cfg)
spc_df = SPC.gen()

spc_df.reset_index(inplace=True)
keylot = spc_df['Lot_ID'].values.tolist()[random.randint(int(data_cnt*0.8), data_cnt-1)]

# %%
################################
# SPC Plotter:
################################
class SpcPlotter:
    # TODO: make a control limit be tightened assuming the process was imporved.
    line_color = [46/255, 117/255, 182/255]
    
    def __init__(self, df, process_name, chart_name, chart_type, chart_descpt, hl_lot, figsize=(16, 5), layout_rect=[0, 0, 0.97, 1]):
        self.df = df
        self.chart_name = chart_name
        self.chart_type = chart_type
        self.chart_descpt = chart_descpt
        self.process_name = process_name
        self.usl = self.df['USL'].values[-1]
        self.lsl = self.df['LSL'].values[-1]
        self.ucl = self.df['UCL'].values[-1]
        self.lcl = self.df['LCL'].values[-1]
        self.val_max = self.df['Value'].max()
        self.val_min = self.df['Value'].min()
        self.val_abs_max = self.df['Value'].abs().max()
        self.val_abs_min = self.df['Value'].abs().min()
        self.abs_sl = max(abs(self.usl), abs(self.lsl))
        self.abs_cl = max(abs(self.ucl), abs(self.lcl))
        self.hl_lot = hl_lot
        self.hl_lot_index = []
        self.figsize = figsize
        self.layout_rect = layout_rect
        self.fig, self.ax = plt.subplots(1, 1, figsize=self.figsize)

    def gen_xticklabels(self):
        if len(self.df) <= 20:
            self.tick_step = 1
        elif len(self.df) > 20 and len(self.df) <= 50:
            self.tick_step = 2
        elif len(self.df) > 50 and len(self.df) <= 100:
            self.tick_step = 3
        elif len(self.df) > 100 and len(self.df) <= 300:
            self.tick_step = 4
        else:
            self.tick_step = 5

        self.tick_id = np.arange(0, len(self.df), self.tick_step)
        self.x_label = [datetime.strftime(x, '%y/%m/%d-%H:%M:%S') for x in self.df['Data_Time'][self.tick_id]]

    def set_title(self):
        self.ax.set_title('Title: [{0:s}][{1:s}][{2:s}][{3:s}]'.format(
            self.process_name, self.chart_name, self.chart_type, self.chart_descpt
            ),fontsize=8, loc='left')

    def set_xyaxis(self):
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

    def set_xrange(self):
        self.ax.set_xlim([-len(self.df)*0.01, (len(self.df)-1)*1.01])

    def set_xaxis(self):
        self.ax.set_xticks(self.tick_id)
        self.ax.set_xticklabels(self.x_label, rotation=90)
            
    def set_yaxis(self):
        self.ax.tick_params(axis='y', which='minor', direction="out")

    def plot_target(self):
        if self.chart_type == 'MEAN':
            self.ax.plot(self.df['index'], np.zeros(len(self.df)), ':', color=[84 / 255, 130 / 255, 53 / 255])
            self.ax.text((len(self.df) - 1) * 1.01, 0, 'Target', color=[84 / 255, 130 / 255, 53 / 255], va='center')

    def plot_cl(self):
        self.ax.plot(self.df['index'], self.df['UCL'], '--', color='r')
        self.ax.text((len(self.df)-1)*1.01, self.ucl, 'UCL', color='r', va='center')
        self.ax.plot(self.df['index'], self.df['LCL'], '--', color='r')
        self.ax.text((len(self.df) - 1) * 1.01, self.lcl, 'LCL', color='r', va='center')

    def plot_sl(self):
        self.ax.plot(self.df['index'], self.df['USL'], '-', color='r')
        self.ax.plot(self.df['index'], self.df['LSL'], '-', color='r')

    def text_usl(self):
        ymin, ymax = self.ax.get_ylim()
        if self.usl < ymax and self.ucl / self.usl <= 0.95:
            self.ax.text((len(self.df) - 1) * 1.01, self.usl, 'USL', color='r', va='center')
            print("Set USL")
    
    def text_lsl(self):
        ymin, ymax = self.ax.get_ylim()
        if self.lsl > ymin and self.lcl / self.lsl <= 0.95:
            self.ax.text((len(self.df) - 1) * 1.01, self.lsl, 'LSL', color='r', va='center')
            print("Set LSL")

    def set_yrange(self):
        if self.chart_type == 'MEAN':
            self.ax.set_ylim(self.lcl * 1.25, self.ucl * 1.25)
            if (self.val_abs_max >= self.abs_sl*1.5) and (self.val_abs_max < self.abs_sl*2):
                self.ax.set_ylim(-self.val_abs_max * 1.05, self.val_abs_max * 1.05)
            elif (self.val_abs_max >= self.abs_sl*2):
                self.ax.set_ylim(-self.abs_sl * 2, self.abs_sl * 2)
                # self.df['Value'].loc[self.df[self.df['Value'] >= self.usl * 2]] = self.usl * 1.95

        if self.chart_type == 'RANGE':
            self.ax.set_ylim(0, self.ucl * 1.5)
            if (self.val_abs_max >= self.abs_sl*1.5) and (self.val_abs_max < self.abs_sl*2):
                self.ax.set_ylim(0, self.val_abs_max * 1.05)
            elif (self.val_abs_max >= self.abs_sl*2):
                self.ax.set_ylim(0, self.abs_sl * 2)
        
        self.ymin, self.ymax = self.ax.get_ylim()
        self.text_usl()
        self.text_lsl()


    def set_ooc(self):
        ymin, ymax = self.ax.get_ylim()
        self.ooc_index = list(self.df[(self.df['Value'] >= self.df['UCL']) | (self.df['Value'] <= self.df['LCL'])].index)
        
        self.out_of_ymax = list(self.df[(self.df['Value'] >= ymax)].index)
        if self.out_of_ymax:
            self.df['Value'].loc[self.out_of_ymax] = ymax * 0.98

        if self.chart_type != 'RANGE':
            self.out_of_ymin = list(self.df[(self.df['Value'] <= ymin)].index)
            if self.out_of_ymin:
                self.df['Value'].loc[self.out_of_ymin] = ymin * 0.98

    def plot_value(self):
        self.ax.plot(self.df['index'], self.df['Value'], '-o', color=line_color)
        if self.ooc_index:
            self.ax.plot(self.ooc_index, self.df['Value'].loc[self.ooc_index], 'ro')

    def hightlight_lot(self):
        ymin, ymax = self.ax.get_ylim()
        self.hl_lot_index = self.df[self.df['Lot_ID'] == self.hl_lot].index.tolist()
        if self.hl_lot_index:
            for hl in self.hl_lot_index:
                _ = self.ax.add_patch(RT((hl-0.5, ymin), 1, ymax - ymin, facecolor='m', alpha=0.3))

    def plot(self):
        self.gen_xticklabels()
        self.set_title()
        self.set_xyaxis()
        self.set_xrange()
        self.set_xaxis()
        self.plot_cl()
        self.plot_sl()
        self.set_yrange()
        self.set_yaxis()
        self.plot_target()
        self.set_ooc()
        self.plot_value()
        self.hightlight_lot()
        plt.tight_layout(rect=self.layout_rect)
        plt.show()

# %%
Plotter = SpcPlotter(spc_df, process_name, chart_name, chart_type, chart_descpt, keylot)
Plotter.plot()
fig, ax = Plotter.fig, Plotter.ax

# %%
fig_name = '#'.join(['chart', keylot, process_name, chart_name, chart_type])
fig.savefig('./output/{}.png'.format(fig_name), dpi=150)
