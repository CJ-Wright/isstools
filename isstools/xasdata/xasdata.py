import numpy as np
import matplotlib.pyplot as plt
import math
import os
from bluesky.global_state import gs
from databroker import (DataBroker as db, get_events, get_images,
                        get_table, get_fields, restream, process)
from datetime import datetime
from isstools.conversions import xray

class XASdata:
    def __init__(self, **kwargs):
        self.energy = np.array([])
        self.data = np.array([])
        self.encoder_file = ''
        self.i0_file = ''
        self.it_file = ''
        self.ir_file = ''
        self.data_manager = XASDataManager()
        self.header_read = ''

    def loadADCtrace(self, filename = '', filepath = '/GPFS/xf08id/pizza_box_data/'):
        array_out=[]
        with open(filepath + str(filename)) as f:
            for line in f:
                current_line = line.split()
                current_line[3] = int(current_line[3],0) >> 8
                if current_line[3] > 0x1FFFF:
                    current_line[3] -= 0x40000
                current_line[3] = float(current_line[3]) * 7.62939453125e-05
                array_out.append(
                        [int(current_line[0])+1e-9*int(current_line[1]), current_line[3], int(current_line[2])])
        return np.array(array_out)

    def loadENCtrace(self, filename = '', filepath = '/GPFS/xf08id/pizza_box_data/'):
        array_out = []
        with open(filepath + str(filename)) as f:
            for line in f:  # read rest of lines
                current_line = line.split()
                array_out.append([int(current_line[0])+1e-9*int(current_line[1]), int(current_line[2]), int(current_line[3])])
        return np.array(array_out)

    def loadTRIGtrace(self, filename = '', filepath = '/GPFS/xf08id/pizza_box_data/'):
        array_out = []
        with open(filepath + str(filename)) as f:
            for line in f:  # read rest of lines
                current_line = line.split()
                if(int(current_line[4]) != 0):
                    array_out.append([int(current_line[0])+1e-9*int(current_line[1]), int(current_line[3])])
        return np.array(array_out)

    def loadINTERPtrace(self, filename):
        array_timestamp=[]
        array_energy=[]
        array_i0=[]
        array_it=[]
        array_ir=[]
        with open(str(filename)) as f:
            for line in f:
                current_line = line.split()
                if(current_line[0] != '#'):
                    array_timestamp.append(float(current_line[0]))
                    array_energy.append(float(current_line[1]))
                    array_i0.append(float(current_line[2]))
                    array_it.append(float(current_line[3]))
                    if len(current_line) == 5:
                        array_ir.append(float(current_line[4]))
        self.header_read = self.read_header(filename)
        ts, energy, i0, it, ir = np.array(array_timestamp), np.array(array_energy), np.array(array_i0), np.array(array_it), np.array(array_ir)
        return np.concatenate(([ts], [energy])).transpose(), np.concatenate(([ts], [i0])).transpose(),np.concatenate(([ts], [it])).transpose(), np.concatenate(([ts], [ir])).transpose()
        
    def read_header(self, filename):
        with open(filename) as myfile:
            return ''.join(str(elem) for elem in [next(myfile) for x in range(12)])


class XASdataAbs(XASdata):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i0 = np.array([])
        self.it = np.array([])
        self.ir = np.array([])

    def process(self, encoder_trace, i0trace, ittrace, irtrace = '', i0offset = 0, itoffset = 0, iroffset = 0):
        self.load(encoder_trace, i0trace, ittrace, irtrace, i0offset, itoffset, iroffset)
        self.interpolate()
        self.plot()

    def load(self, encoder_trace, i0trace, ittrace, irtrace = '', i0offset = 0, itoffset = 0, iroffset = 0):
        self.encoder_file = encoder_trace
        self.i0_file = i0trace
        self.it_file = ittrace
        self.ir_file = irtrace
        self.encoder = self.loadENCtrace(encoder_trace)
        self.energy = self.encoder
        #self.energy[:, 1] = xray.encoder2energy(self.encoder[:, 1], 0.041)
        self.energy[:, 1] = xray.encoder2energy(self.encoder[:, 1], 0) #-12400 / (2 * 3.1356 * np.sin((np.pi / 180) * ((self.encoder[:, 1]/360000) + 0)))
        self.i0 = self.loadADCtrace(i0trace)
        self.it = self.loadADCtrace(ittrace)
        self.ir = self.loadADCtrace(irtrace)
        self.i0[:, 1] = self.i0[:, 1] - i0offset
        self.it[:, 1] = self.it[:, 1] - itoffset
        self.ir[:, 1] = self.ir[:, 1] - iroffset

    def loadInterpFile(self, filename):
        self.energy_interp, self.i0_interp, self.it_interp, self.ir_interp = self.loadINTERPtrace(filename)

    def interpolate(self):
        min_timestamp = np.array([self.i0[0,0], self.it[0,0], self.ir[0,0], self.encoder[0,0]]).max()
        max_timestamp = np.array([self.i0[len(self.i0)-1,0], self.it[len(self.it)-1,0], self.ir[len(self.ir)-1,0], self.encoder[len(self.encoder)-1,0]]).min()
        interval = self.i0[1,0] - self.i0[0,0]
        timestamps = np.arange(min_timestamp, max_timestamp, interval)
        self.i0_interp = np.array([timestamps, np.interp(timestamps, self.i0[:,0], self.i0[:,1])]).transpose()
        self.it_interp = np.array([timestamps, np.interp(timestamps, self.it[:,0], self.it[:,1])]).transpose()
        self.ir_interp = np.array([timestamps, np.interp(timestamps, self.ir[:,0], self.ir[:,1])]).transpose()
        self.energy_interp = np.array([timestamps, np.interp(timestamps, self.energy[:,0], self.energy[:,1])]).transpose()

    def plot(self, ax = plt, color = 'r', derivative = True ):
        result_chambers = np.copy(self.i0_interp)
        result_chambers[:,1] = np.log(self.i0_interp[:,1] / self.it_interp[:,1])
        ax.plot(self.energy_interp[:,1], result_chambers[:,1], color)
        ax.grid(True)
        if 'xlabel' in dir(ax):
            ax.xlabel('Energy (eV)')
            ax.ylabel('log(i0 / it)')
        elif 'set_xlabel' in dir(ax):
            ax.set_xlabel('Energy (eV)')
            ax.set_ylabel('log(i0 / it)')

    def export_trace(self, filename, filepath = '/GPFS/xf08id/Sandbox/', uid = ''):
        suffix = '.txt'
        fn = filepath + filename + suffix
        repeat = 1
        while(os.path.isfile(fn)):
            repeat += 1
            fn = filepath + filename + '-' + str(repeat) + suffix
        if(not uid):
            pi, proposal, saf, comment, year, cycle, scan_id, real_uid, start_time, stop_time = '', '', '', '', '', '', '', '', '', ''
        else:
            pi, proposal, saf, comment, year, cycle, scan_id, real_uid, start_time, stop_time = db[uid]['start']['PI'], db[uid]['start']['PROPOSAL'], db[uid]['start']['SAF'], db[uid]['start']['comment'], db[uid]['start']['year'], db[uid]['start']['cycle'], db[uid]['start']['scan_id'], db[uid]['start']['uid'], db[uid]['start']['time'], db[uid]['stop']['time']
            human_start_time = str(datetime.fromtimestamp(start_time).strftime('%m/%d/%Y  %H:%M:%S'))
            human_stop_time = str(datetime.fromtimestamp(stop_time).strftime(' %m/%d/%Y  %H:%M:%S'))
            human_duration = str(datetime.fromtimestamp(stop_time - start_time).strftime('%M:%S'))
        
        np.savetxt(fn, np.array([self.energy_interp[:,0], self.energy_interp[:,1], 
                    self.i0_interp[:,1], self.it_interp[:,1], self.ir_interp[:,1]]).transpose(), fmt='%17.6f %8.2f %f %f %f', 
                    delimiter=" ", header = 'Timestamp (s)   En. (eV)     i0 (V)      it(V)       ir(V)', comments = '# Year: {}\n# Cycle: {}\n# SAF: {}\n# PI: {}\n# PROPOSAL: {}\n# Scan ID: {}\n# UID: {}\n# Start time: {}\n# Stop time: {}\n# Total time: {}\n#\n# '.format(year, cycle, saf, pi, proposal, scan_id, real_uid, human_start_time, human_stop_time, human_duration))
        return fn


    def bin_equal(self):
        self.data_manager.process_equal(self.i0_interp[:,0], 
                                  self.energy_interp[:,1],
                                  self.i0_interp[:,1],
                                  self.it_interp[:,1], 
                                  self.ir_interp[:,1])

    def bin(self, e0, edge_start, edge_end, preedge_spacing, xanes, exafsk):
        self.data_manager.process(self.i0_interp[:,0], 
                                  self.energy_interp[:,1],
                                  self.i0_interp[:,1],
                                  self.it_interp[:,1], 
                                  self.ir_interp[:,1],
                                  e0, edge_start, edge_end,
                                  preedge_spacing, xanes, exafsk)


class XASdataFlu(XASdata):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i0 = np.array([])
        self.trigger = np.array([])
        self.iflu = np.array([])
        self.it = np.array([])
        self.ir = np.array([])
        self.trig_file = ''

    def process(self, encoder_trace, i0trace, iflutrace, irtrace = '', trigtrace = '', i0offset = 0, ifluoffset = 0, iroffset = 0):
        self.load(encoder_trace, i0trace, iflutrace, irtrace, trigtrace, i0offset, ifluoffset, iroffset)
        self.interpolate()
        self.plot()

    def load(self, encoder_trace, i0trace, iflutrace, irtrace = '', trigtrace = '', i0offset = 0, ifluoffset = 0, iroffset = 0):
        self.encoder_file = encoder_trace
        self.i0_file = i0trace
        self.it_file = iflutrace
        self.ir_file = irtrace
        self.trig_file = trigtrace
        self.encoder = self.loadENCtrace(encoder_trace)
        self.energy = np.copy(self.encoder)
        #self.energy[:, 1] = xray.encoder2energy(self.encoder[:, 1], 0.041)
        self.energy[:, 1] = xray.encoder2energy(self.encoder[:, 1], 0)
        self.i0 = self.loadADCtrace(i0trace)
        self.i0[:, 1] = self.i0[:, 1] - i0offset
        self.ir = self.loadADCtrace(irtrace)
        self.ir[:, 1] = self.ir[:, 1] - iroffset
        self.iflu = self.loadADCtrace(iflutrace)
        self.iflu[:, 1] = self.iflu[:, 1] - ifluoffset
        self.trigger = self.loadTRIGtrace(trigtrace)
        self.it = np.copy(self.iflu)


    def loadInterpFile(self, filename):
        self.energy_interp, self.i0_interp, self.iflu_interp, self.ir_interp = self.loadINTERPtrace(filename)

    def interpolate(self):
        i0_copy = np.copy(self.i0)
        iflu_copy = np.copy(self.iflu)
        ir_copy = np.copy(self.ir)
        energy_copy = np.copy(self.energy)
        i0_interp = []
        iflu_interp = []
        ir_interp = []
        energy_interp = []
        trigger_interp = []
        timestamps = []

        for i in range(len(self.trigger) - 1):

            condition1 = (self.trigger[i,0] <= i0_copy[:,0]) == (self.trigger[i + 1,0] > i0_copy[:,0])
            interval1 = np.extract(condition1, i0_copy[:,0])

            condition2 = (self.trigger[i,0] <= iflu_copy[:,0]) == (self.trigger[i + 1,0] > iflu_copy[:,0])
            interval2 = np.extract(condition2, iflu_copy[:,0])

            condition3 = (self.trigger[i,0] <= energy_copy[:,0]) == (self.trigger[i + 1,0] > energy_copy[:,0])
            interval3 = np.extract(condition3, energy_copy[:,0])

            condition4 = (self.trigger[i,0] <= ir_copy[:,0]) == (self.trigger[i + 1,0] > ir_copy[:,0])
            interval4 = np.extract(condition4, ir_copy[:,0])

            if len(interval1) and len(interval2) and len(interval3):
                interval_mean_i0 = np.mean(np.extract(condition1, i0_copy[:,1]))
                i0_interp.append(interval_mean_i0)
                i0_pos_high = np.where( i0_copy[:,0] == interval1[len(interval1) - 1] )[0][0]
                i0_copy = i0_copy[i0_pos_high + 1:len(i0_copy)]


                interval_mean_iflu = np.mean(np.extract(condition2, iflu_copy[:,1]))
                iflu_interp.append(interval_mean_iflu)
                iflu_pos_high = np.where( iflu_copy[:,0] == interval2[len(interval2) - 1] )[0][0]
                iflu_copy = iflu_copy[iflu_pos_high + 1:len(iflu_copy)]


                interval_mean_energy = np.mean(np.extract(condition3, energy_copy[:,1]))
                energy_interp.append(interval_mean_energy)
                energy_pos_high = np.where( energy_copy[:,0] == interval3[len(interval3) - 1] )[0][0]
                energy_copy = energy_copy[energy_pos_high + 1:len(energy_copy)]


                interval_mean_ir = np.mean(np.extract(condition4, ir_copy[:,1]))
                ir_interp.append(interval_mean_ir)
                ir_pos_high = np.where( ir_copy[:,0] == interval4[len(interval4) - 1] )[0][0]
                ir_copy = ir_copy[ir_pos_high + 1:len(ir_copy)]

                timestamps.append((self.trigger[i, 0] + self.trigger[i + 1, 0])/2)
                trigger_interp.append(self.trigger[i, 1])

        self.i0_interp = np.array([timestamps, i0_interp]).transpose()
        self.iflu_interp = np.array([timestamps, iflu_interp]).transpose()
        self.ir_interp = np.array([timestamps, ir_interp]).transpose()
        #self.it_interp = np.copy(self.iflu_interp)
        self.energy_interp = np.array([timestamps, energy_interp]).transpose()
        self.trigger_interp = np.array([timestamps, trigger_interp]).transpose()


    def plot(self, ax=plt, color='r'):
        result_chambers = np.copy(self.i0_interp)
        result_chambers[:,1] = (self.iflu_interp[:,1] / self.i0_interp[:,1])

        ax.plot(self.energy_interp[:,1], result_chambers[:,1], color)
        ax.grid(True)
        if 'xlabel' in dir(ax):
            ax.xlabel('Energy (eV)')
            ax.ylabel('(iflu / i0)')
        elif 'set_xlabel' in dir(ax):
            ax.set_xlabel('Energy (eV)')
            ax.set_ylabel('(iflu / i0)')





    def export_trace(self, filename, filepath = '/GPFS/xf08id/Sandbox/', uid = ''):
        suffix = '.txt'
        fn = filepath + filename + suffix
        repeat = 1
        while(os.path.isfile(fn)):
            repeat += 1
            fn = filepath + filename + '-' + str(repeat) + suffix
        if(not uid):
            pi, proposal, saf, comment, year, cycle, scan_id, real_uid, start_time, stop_time = '', '', '', '', '', '', '', '', '', ''
        else:
            pi, proposal, saf, comment, year, cycle, scan_id, real_uid, start_time, stop_time = db[uid]['start']['PI'], db[uid]['start']['PROPOSAL'], db[uid]['start']['SAF'], db[uid]['start']['comment'], db[uid]['start']['year'], db[uid]['start']['cycle'], db[uid]['start']['scan_id'], db[uid]['start']['uid'], db[uid]['start']['time'], db[uid]['stop']['time']
            human_start_time = str(datetime.fromtimestamp(start_time).strftime('%m/%d/%Y  %H:%M:%S'))
            human_stop_time = str(datetime.fromtimestamp(stop_time).strftime(' %m/%d/%Y  %H:%M:%S'))
            human_duration = str(datetime.fromtimestamp(stop_time - start_time).strftime('%M:%S'))
        
        np.savetxt(fn, np.array([self.energy_interp[:,0], self.energy_interp[:,1], 
                    self.i0_interp[:,1], self.iflu_interp[:,1], self.ir_interp[:,1]]).transpose(), fmt='%17.6f %8.2f %f %f %f', 
                    delimiter=" ", header = 'Timestamp (s)   En. (eV)   i0 (V)    iflu(V)   ir(V)', comments = '# Year: {}\n# Cycle: {}\n# SAF: {}\n# PI: {}\n# PROPOSAL: {}\n# Scan ID: {}\n# UID: {}\n# Start time: {}\n# Stop time: {}\n# Total time: {}\n#\n# '.format(year, cycle, saf, pi, proposal, scan_id, real_uid, human_start_time, human_stop_time, human_duration))
        return fn




    def export_trace_xia(self, parsed_xia_array, filename, filepath = '/GPFS/xf08id/Sandbox/', uid = ''):
        parsed_xia_array = np.array(parsed_xia_array)
        suffix = '.txt'
        fn = filepath + filename + suffix
        repeat = 1
        while(os.path.isfile(fn)):
            repeat += 1
            fn = filepath + filename + '-' + str(repeat) + suffix
        if(not uid):
            pi, proposal, saf, comment, year, cycle, scan_id, real_uid, start_time, stop_time = '', '', '', '', '', '', '', '', '', ''
        else:
            pi, proposal, saf, comment, year, cycle, scan_id, real_uid, start_time, stop_time = db[uid]['start']['PI'], db[uid]['start']['PROPOSAL'], db[uid]['start']['SAF'], db[uid]['start']['comment'], db[uid]['start']['year'], db[uid]['start']['cycle'], db[uid]['start']['scan_id'], db[uid]['start']['uid'], db[uid]['start']['time'], db[uid]['stop']['time']
            human_start_time = str(datetime.fromtimestamp(start_time).strftime('%m/%d/%Y  %H:%M:%S'))
            human_stop_time = str(datetime.fromtimestamp(stop_time).strftime(' %m/%d/%Y  %H:%M:%S'))
            human_duration = str(datetime.fromtimestamp(stop_time - start_time).strftime('%M:%S'))
        
        np.savetxt(fn, np.array([self.energy_interp[:,0], self.energy_interp[:,1], 
                    self.i0_interp[:,1], self.iflu_interp[:,1], parsed_xia_array]).transpose(), fmt='%17.6f %8.2f %f %f', 
                    delimiter=" ", header = 'Timestamp (s)   En. (eV)  i0 (V)    iflu(V)   xia', comments = '# Year: {}\n# Cycle: {}\n# SAF: {}\n# PI: {}\n# PROPOSAL: {}\n# Scan ID: {}\n# UID: {}\n# Start time: {}\n# Stop time: {}\n# Total time: {}\n#\n# '.format(year, cycle, saf, pi, proposal, scan_id, real_uid, human_start_time, human_stop_time, human_duration))
        return fn




    def export_trig_trace(self, filename, filepath = '/GPFS/xf08id/Sandbox/'):
        np.savetxt(filepath + filename + suffix, self.energy_interp[:,1], fmt='%f', delimiter=" ")


class XASDataManager:
    def __init__(self, *args, **kwargs):
        pass

    def delta_energy(self, array):
        diff = np.diff(array)
        diff = np.concatenate((diff,[diff[len(diff)-1]]))
        out = (np.concatenate(([diff[0]], diff[:len(diff)-1])) + diff)/2
        return out
    
    def sort_data(self, matrix, column_to_sort):
        return matrix[matrix[:,column_to_sort].argsort()]
    
    def energy_grid_equal(self, array, interval):
        return np.arange(np.min(array), np.max(array) + interval/2, interval)
    
    def energy_grid(self, array, e0, edge_start, edge_end, preedge_spacing, xanes, exafsk):
        preedge = np.arange(np.min(array), edge_start, preedge_spacing)
        edge = np.arange(edge_start, edge_end, xanes)

        iterator = exafsk
        kenergy = 0
        postedge = np.array([])

        while(kenergy + edge_end < np.max(array)):
            kenergy = xray.k2e(iterator, e0) - e0
            postedge = np.append(postedge, edge_end + kenergy)
            iterator += exafsk

        return np.append(np.append(preedge, edge), postedge)
    
    def gauss(self, x, fwhm, x0):
        sigma = fwhm / (2 * ((np.log(2)) ** (1/2)))
        a = 1/(sigma * ((2 * np.pi) ** (1/2)))
        data_y = a * np.exp(-.5 * ((x - x0) / sigma) ** 2)
        data_y = np.array(data_y / sum(data_y))
        return data_y
    
    def bin(self, en_st, data_x, data_y):
        buf = self.delta_energy(en_st)
        mat = []
        for i in range(len(buf)):
            line = self.gauss(data_x, buf[i], en_st[i])
            mat.append(line)
        data_st = np.matmul(np.array(mat), data_y)
        return data_st.transpose()

    def plot(self, ax=plt, color='b'):
        ax.plot(self.en_grid, self.abs, color)
        ax.grid(True)
        if 'xlabel' in dir(ax):
            ax.xlabel('Energy (eV)')
            ax.ylabel('Log(i0 / it)')
        elif 'set_xlabel' in dir(ax):
            ax.set_xlabel('Energy (eV)')
            ax.set_ylabel('Log(i0 / it)')    


    def plot_der(self, ax=plt, color='b'):
        ax.plot(self.en_grid, self.abs_der, color)
        ax.grid(True)
        if 'xlabel' in dir(ax):
            ax.xlabel('Energy (eV)')
            ax.ylabel('(iflu / i0)')
        elif 'set_xlabel' in dir(ax):
            ax.set_xlabel('Energy (eV)')
            ax.set_ylabel('(iflu / i0)')    


    def export_dat(self, filename, header = ''):
        filename = filename[0: len(filename) - 3] + 'dat'
        np.savetxt(filename, np.array([self.en_grid, self.i0, self.it, self.ir]).transpose(), fmt='%.7e %15.7e %15.7e %15.7e', comments = '', header = header)


    def plot_orig(self, ax=plt, color='r'):
        ax.plot(self.sorted_matrix[:, 1], np.log(self.sorted_matrix[:, 2]/self.sorted_matrix[:, 3]), color)
        ax.grid(True)
        if 'xlabel' in dir(ax):
            ax.xlabel('Energy (eV)')
            ax.ylabel('(iflu / i0)')
        elif 'set_xlabel' in dir(ax):
            ax.set_xlabel('Energy (eV)')
            ax.set_ylabel('(iflu / i0)')    


    def process(self, timestamp, energy, i0, it, ir, e0, edge_start, edge_end, preedge_spacing, xanes, exafsk):
        self.ts_orig = timestamp
        self.en_orig = energy
        self.i0_orig = i0
        self.it_orig = it
        self.ir_orig = ir

        self.matrix = np.array([timestamp, energy, i0, it, ir]).transpose()  
        self.sorted_matrix = self.sort_data(self.matrix, 1)
        self.en_grid = self.energy_grid(self.sorted_matrix[:, 1], e0, edge_start, edge_end, preedge_spacing, xanes, exafsk)
        self.data_en = self.sorted_matrix[:, 1]
        self.data_i0 = self.sorted_matrix[:, 2]
        self.data_it = self.sorted_matrix[:, 3]
        self.data_ir = self.sorted_matrix[:, 4]
        self.i0 = self.bin(self.en_grid, self.data_en, self.data_i0)
        self.it = self.bin(self.en_grid, self.data_en, self.data_it)
        self.ir = self.bin(self.en_grid, self.data_en, self.data_ir)
        self.abs = np.log(self.i0/self.it)

        self.abs_der = np.diff(self.abs)
        self.abs_der = np.append(self.abs_der[0], self.abs_der)

    def process_equal(self, timestamp, energy, i0, it, ir, delta_en = 1):
        self.ts_orig = timestamp
        self.en_orig = energy
        self.i0_orig = i0
        self.it_orig = it
        self.ir_orig = ir

        self.matrix = np.array([timestamp, energy, i0, it, ir]).transpose()  
        self.sorted_matrix = self.sort_data(self.matrix, 1)
        self.en_grid = self.energy_grid_equal(self.sorted_matrix[:, 1], delta_en)
        self.data_en = self.sorted_matrix[:, 1]
        self.data_i0 = self.sorted_matrix[:, 2]
        self.data_it = self.sorted_matrix[:, 3]
        self.data_ir = self.sorted_matrix[:, 4]
        self.i0 = self.bin(self.en_grid, self.data_en, self.data_i0)
        self.it = self.bin(self.en_grid, self.data_en, self.data_it)
        self.ir = self.bin(self.en_grid, self.data_en, self.data_ir)
        self.abs = np.log(self.i0/self.it)

        self.abs_der = np.diff(self.abs)
        self.abs_der = np.append(self.abs_der[0], self.abs_der)

        self.abs_der2 = np.diff(self.abs_der)
        self.abs_der2 = np.append(self.abs_der2[0], self.abs_der2)

