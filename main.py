"""

Author: ZhaoZh02
Email: zzh@stu.pku.edu.cn
用于积分雷诺校正，可以方便地拟合直线、给出拟合误差、寻找使积分面积相等的点，并求出校正后的温度。
拯救物化实验
——即使它没了
2022.11.22

使用说明
0. 运行python程序或exe程序，前者需安装numpy和scipy库，后者加载较慢，但你先别急。推荐使用python。
1. 点击File导入文件。
2. csv或txt文件格式：两列纯数据，第一列为升序的time(s)，第二列Delta_T(K)；同一行数据间以半角逗号分隔。
3. 调整Start 1 < End 1 < Start 2 < End 2至合适位置，推荐单击输入栏后使用键盘↑↓进行调节，报错可以Remake。
4. 点击Integrate积分。
5. 点击Save按钮保存png格式图片，与数据文件位于同一目录。也可使用下方matplotlib控件，若显示不全请调整窗口大小。

可修改的参数
1. 图片坐标轴和刻度，位于# set spines and ticks (line 46)
2. 图片点、线、积分面积等，位于函数def dynamic_plot (line 517)、def Reynolds_plot (line 543)。
3. 积分步长，位于def Reynolds (line 465)，默认值dx = 0.005，dx过小将使积分时间过长。
P.S. 寻找积分面积相等的点本来可以写二分法的，但不改也不耽误用所以就懒了。

License
MIT License

"""

import ctypes
from tkinter import *
#from tkinter.ttk import *  # ttk can beautify tkinter
import tkinter.filedialog as filedialog
from tkinter.messagebox import *
import numpy as np
from scipy import optimize, interpolate
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# define global varaibles
path = "Waiting for your file..."
csv = None
start1, end1, start2, end2 = None, None, None, None   # 0 <= start1 < end1 < start2 < end2 < len(csv)
len_csv = 4
# set spines and ticks
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
rcParams['font.family']='sans-serif'
rcParams['font.sans-serif']=['Arial'] # Arial
ax = plt.gca()
ax.spines['top'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)
ax.spines['left'].set_linewidth(0.5)
ax.spines['right'].set_linewidth(0.5)
plt.xlabel("$t$ (s)")
plt.ylabel("$\Delta T$ (K)")
# init figure
P = Figure()
f = P.add_subplot(111)
f.set_xlabel("$t$ (s)")
f.set_ylabel("$\Delta T$ (K)")

#
def openfile():
    global path, csv, len_csv, start1, end1, start2, end2
    global listbox_csv, label_path, frame_left_3, button_save, button_integrate, button_remake, entry_start1, entry_end1, entry_start2, entry_end2
    # check
    if len_csv < 4:
        len_csv = 4
    # refresh entries
    reset_entries()
    # read new file
    path = filedialog.askopenfilename(filetypes = [("ALL", "*.*"), ("CSV", ".csv"), ("TXT", ".txt")])
    file_path, file_name = path_name(path)
    label_path.destroy()
    label_path = Label(frame_left_3, text = file_name, height = 2)
    label_path.pack(fill = BOTH)
    with open(path, encoding = 'UTF-8') as f:
        csv = np.loadtxt(path, delimiter = ',')
    # set initial values
    len_csv = len(csv)
    end2.set(str(int(len_csv * 1.00 - 1)))
    start2.set(str(int(len_csv * 0.75 - 1)))
    end1.set(str(int(len_csv * 0.25)))
    start1.set(str(int(len_csv * 0.00)))
    entry_end2.destroy()
    entry_end2 = Spinbox(frame_right_2_middle, textvariable = end2, command = input_end2, from_ = 0, to = len_csv - 1, increment = 1)
    entry_end2.pack(side = LEFT, fill = BOTH, expand = TRUE)
    entry_start2.destroy()
    entry_start2 = Spinbox(frame_right_2_left, textvariable = start2, command = input_start2, from_ = 0, to = len_csv - 1, increment = 1)
    entry_start2.pack(side = LEFT, fill = BOTH, expand = TRUE)
    entry_end1.destroy()
    entry_end1 = Spinbox(frame_right_1_middle, textvariable = end1, command = input_end1, validate = "all", validatecommand = input_end1,from_ = 0, to = len_csv - 1, increment = 1)
    entry_end1.pack(side = LEFT, fill = BOTH, expand = TRUE)
    entry_start1.destroy()
    entry_start1 = Spinbox(frame_right_1_left, textvariable = start1, command = input_start1, from_ = 0, to = len_csv - 1, increment = 1)
    entry_start1.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # fill csv listbox
    listbox_csv.delete(0, listbox_csv.size() - 1)
    listbox_csv.insert(0, "  id    time(s)    Delta_T(K)")
    for i in range(len(csv)):
        listbox_csv.insert(i + 1, "  {}    {}    {}".format(i, csv[i, 0], csv[i, 1]))
    # enable entries
    entry_start1.config(state = NORMAL)
    entry_end1.config(state = NORMAL)
    entry_start2.config(state = NORMAL)
    entry_end2.config(state = NORMAL)
    # regression
    calculate_regression()
    # enable buttons
    button_remake.config(state = NORMAL)
    button_integrate.config(state = NORMAL)
    button_save.config(state = NORMAL)
    return

def reset_entries():
    global path, csv, len_csv, start1, end1, start2, end2
    global listbox_csv, label_path, frame_left_3, button_save, button_integrate, button_remake, entry_start1, entry_end1, entry_start2, entry_end2
    entry_end2.destroy()
    entry_start2.destroy()
    entry_end1.destroy()
    entry_start1.destroy()
    end2.set("3")
    start2.set("2")
    end1.set("1")
    start1.set("0")
    entry_end2 = Spinbox(frame_right_2_middle, textvariable = end2, command = input_end2, from_ = 0, to = len_csv - 1, increment = 1)
    entry_end2.config(state = DISABLED)
    entry_end2.pack(side = LEFT, fill = BOTH, expand = TRUE)
    entry_start2 = Spinbox(frame_right_2_left, textvariable = start2, command = input_start2, from_ = 0, to = len_csv - 1, increment = 1)
    entry_start2.config(state = DISABLED)
    entry_start2.pack(side = LEFT, fill = BOTH, expand = TRUE)
    entry_end1 = Spinbox(frame_right_1_middle, textvariable = end1, command = input_end1, validate = "all", validatecommand = input_end1,from_ = 0, to = len_csv - 1, increment = 1)
    entry_end1.config(state = DISABLED)
    entry_end1.pack(side = LEFT, fill = BOTH, expand = TRUE)
    entry_start1 = Spinbox(frame_right_1_left, textvariable = start1, command = input_start1, from_ = 0, to = len_csv - 1, increment = 1)
    entry_start1.config(state = DISABLED)
    entry_start1.pack(side = LEFT, fill = BOTH, expand = TRUE)
    return

def remakefile():
    global csv, len_csv, start1, end1, start2, end2
    global entry_start1, entry_end1, entry_start2, entry_end2
    reset_entries()
    # set initial values
    len_csv = len(csv)
    end2.set(str(int(len_csv * 1.00 - 1)))
    start2.set(str(int(len_csv * 0.75 - 1)))
    end1.set(str(int(len_csv * 0.25)))
    start1.set(str(int(len_csv * 0.00)))
    entry_end2.destroy()
    entry_end2 = Spinbox(frame_right_2_middle, textvariable = end2, command = input_end2, from_ = 0, to = len_csv - 1, increment = 1)
    entry_end2.pack(side = LEFT, fill = BOTH, expand = TRUE)
    entry_start2.destroy()
    entry_start2 = Spinbox(frame_right_2_left, textvariable = start2, command = input_start2, from_ = 0, to = len_csv - 1, increment = 1)
    entry_start2.pack(side = LEFT, fill = BOTH, expand = TRUE)
    entry_end1.destroy()
    entry_end1 = Spinbox(frame_right_1_middle, textvariable = end1, command = input_end1, validate = "all", validatecommand = input_end1,from_ = 0, to = len_csv - 1, increment = 1)
    entry_end1.pack(side = LEFT, fill = BOTH, expand = TRUE)
    entry_start1.destroy()
    entry_start1 = Spinbox(frame_right_1_left, textvariable = start1, command = input_start1, from_ = 0, to = len_csv - 1, increment = 1)
    entry_start1.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # enable entries
    entry_start1.config(state = NORMAL)
    entry_end1.config(state = NORMAL)
    entry_start2.config(state = NORMAL)
    entry_end2.config(state = NORMAL)
    # regression
    calculate_regression()
    # enable buttons
    button_remake.config(state = NORMAL)
    button_integrate.config(state = NORMAL)
    button_save.config(state = NORMAL)
    return

def path_name(filepath):
    for i in range(len(filepath)):
        if filepath[-1 - i] == '.':
            j = i
        if filepath[-1 - i] == '/' or filepath[-1 - i] == '\\\\':
            file_path = filepath[ : (-1 - i)]
            file_name = filepath[(-i) : (-1 - j)]
            break
    result = [file_path, file_name]     # file_name = file name without .csv
    return result
def savefile():
    global path, P, f
    file_path, file_name = path_name(path)
    P.savefig(fname = ("{}/{}.png".format(file_path, file_name)), dpi = 600)
    showinfo(title = "File Saved", message = "{}.png saved to {}.".format(file_name, file_path))
    return

def calculate_regression():
    global csv, start1, end1, start2, end2
    global text_result
    # check
    if str(type(csv)) == "<class 'NoneType'>":
        return
    End2 = end2.get()
    Start2 = start2.get()
    End1 = end1.get()
    Start1 = start1.get()
    if Start1.isdigit() and End1.isdigit() and Start2.isdigit() and End2.isdigit():
        End2 = int(End2)
        Start2 = int(Start2)
        End1 = int(End1)
        Start1 = int(Start1)
    else:
        return False
    # linear regression
    k1, b1, stddev_k1, stddev_b1, r_square1 = linear_regression(csv, Start1, End1)[0 : 5]
    k2, b2, stddev_k2, stddev_b2, r_square2 = linear_regression(csv, Start2, End2)[0 : 5]
    # print results
    text_result.config(state = NORMAL)
    text_result.delete('1.0', '7.0')
    text_result_1 = "Linear Fit 1: y = ({:.6} ± {:.3})x + ({:.6} ± {:.3}), r-square = {:.6f}\n".format(k1, stddev_k1, b1, stddev_b1, r_square1)
    text_result_2 = "Linear Fit 2: y = ({:.6} ± {:.3})x + ({:.6} ± {:.3}), r-square = {:.6f}\n".format(k2, stddev_k2, b2, stddev_b2, r_square2)
    text_result.insert('1.0', text_result_1)
    text_result.insert('2.0', text_result_2)
    text_result.config(state = DISABLED)
    # plot
    dynamic_plot(csv, Start1, End1, Start2, End2, k1, b1, k2, b2)
    return
def calculate_integrate():
    global path, csv, start1, end1, start2, end2
    global text_result
    # check
    End2 = end2.get()
    Start2 = start2.get()
    End1 = end1.get()
    Start1 = start1.get()
    if Start1.isdigit() and End1.isdigit() and Start2.isdigit() and End2.isdigit():
        End2 = int(End2)
        Start2 = int(Start2)
        End1 = int(End1)
        Start1 = int(Start1)
    else:
        return False
    # linear regression
    k1, b1, stddev_k1, stddev_b1, r_square1 = linear_regression(csv, Start1, End1)[0 : 5]
    k2, b2, stddev_k2, stddev_b2, r_square2 = linear_regression(csv, Start2, End2)[0 : 5]
    # Reynolds
    x0, S1, S2 = Reynolds(csv, Start1, End1, Start2, End2)
    # print results
    text_result.config(state = NORMAL)
    text_result.delete('1.0', '7.0')
    text_result_1 = "Linear Fit 1: y = ({:.6} ± {:.3})x + ({:.6} ± {:.3}), r-square = {:.6f}\n".format(k1, stddev_k1, b1, stddev_b1, r_square1)
    text_result_2 = "Linear Fit 2: y = ({:.6} ± {:.3})x + ({:.6} ± {:.3}), r-square = {:.6f}\n".format(k2, stddev_k2, b2, stddev_b2, r_square2)
    text_result_3 = "x0 = {:.2f} s\n".format(x0)
    T1 = k1 * x0 + b1
    T2 = k2 * x0 + b2
    text_result_4 = "S1 = {:.2f} K·s  S2 = {:.2f} K·s\n".format(S1, S2)
    text_result_5 = "T1 = {:.3f} K  T2 = {:.3f} K\n".format(T1, T2)
    text_result.insert('1.0', text_result_1)
    text_result.insert('2.0', text_result_2)
    text_result.insert('3.0', text_result_3)
    text_result.insert('4.0', text_result_4)
    text_result.insert('5.0', text_result_5)
    text_result.config(state = DISABLED)
    # plot
    Reynolds_plot(csv, Start1, End1, Start2, End2, k1, b1, k2, b2, x0)
    return

def input_start1():
    global csv, start1, end1, start2, end2
    global text_result, entry_start1, frame_right_1_left, button_save, button_integrate
    # check
    End2 = end2.get()
    Start2 = start2.get()
    End1 = end1.get()
    Start1 = start1.get()
    if Start1.isdigit() and End1.isdigit() and Start2.isdigit() and End2.isdigit():
        End2 = int(End2)
        Start2 = int(Start2)
        End1 = int(End1)
        Start1 = int(Start1)
    else:
        return False
    """
    # IntVar() can't be upgraded, show warning in the plot instead.
    if Start1 >= End1:
        start1.set(End1 - 1)
        entry_start1 = Spinbox(frame_right_1_left, textvariable = start1, validate = "all", validatecommand = input_start1, from_ = 0, to = end1.get() - 1, increment = 1)
        entry_start1.pack(side = LEFT, fill = BOTH, expand = TRUE)
        return False
    elif Start1 < 0:
        start1.set(0)
        entry_start1 = Spinbox(frame_right_1_left, textvariable = start1, validate = "all", validatecommand = input_start1, from_ = 0, to = end1.get() - 1, increment = 1)
        entry_start1.pack(side = LEFT, fill = BOTH, expand = TRUE)
        return False
    """
    if Start1 >= 0 and Start1 < End1:
        calculate_regression()
        button_save.config(state = NORMAL)
        button_integrate.config(state = NORMAL)
        return True
    else:
        # invalid value
        wrong_plot(csv, Start1, End1, Start2, End2)
        text_result.config(state = NORMAL)
        text_result.delete('1.0', '7.0')
        text_result.insert('1.0', "Required: 0 <= Start 1 < End 1 < Start 2 < End 2 <= max(id)\n")
        text_result.insert('2.0', "You can click Remake.\n")
        text_result.config(state = DISABLED)
        button_save.config(state = DISABLED)
        button_integrate.config(state = DISABLED)
        showinfo(title = "Warning", message = "Required: 0 <= Start 1 < End 1 < Start 2 < End 2 <= max(id)\nYou can click Remake.\n")
        return False
def input_end1():
    global csv, start1, end1, start2, end2
    global text_result, entry_end1, frame_right_1_middle, button_save, button_integrate
    # check
    End2 = end2.get()
    Start2 = start2.get()
    End1 = end1.get()
    Start1 = start1.get()
    if Start1.isdigit() and End1.isdigit() and Start2.isdigit() and End2.isdigit():
        End2 = int(End2)
        Start2 = int(Start2)
        End1 = int(End1)
        Start1 = int(Start1)
    else:
        return False
    """
    # IntVar() can't be upgraded, show warning in the plot instead.
    if End1 <= Start1:
        end1.set(Start1 + 1)
        entry_end1 = Spinbox(frame_right_1_middle, textvariable = end1, validate = "all", validatecommand = input_end1, from_ = start1.get() + 1, to = start2.get() - 1, increment = 1)
        entry_end1.pack(side = LEFT, fill = BOTH, expand = TRUE)
        return False
    elif End1 >= Start2:
        end1.set(Start2 - 1)
        entry_end1 = Spinbox(frame_right_1_middle, textvariable = end1, validate = "all", validatecommand = input_end1, from_ = start1.get() + 1, to = start2.get() - 1, increment = 1)
        entry_end1.pack(side = LEFT, fill = BOTH, expand = TRUE)
        return False
    """
    if End1 > Start1 and End1 < Start2:
        calculate_regression()
        button_save.config(state = NORMAL)
        button_integrate.config(state = NORMAL)
        return True
    else:
        # invalid value
        wrong_plot(csv, Start1, End1, Start2, End2)
        text_result.config(state = NORMAL)
        text_result.delete('1.0', '7.0')
        text_result.insert('1.0', "Required: 0 <= Start 1 < End 1 < Start 2 < End 2 <= max(id)\n")
        text_result.insert('2.0', "You can click Remake.\n")
        text_result.config(state = DISABLED)
        button_save.config(state = DISABLED)
        button_integrate.config(state = DISABLED)
        showinfo(title = "Warning", message = "Required: 0 <= Start 1 < End 1 < Start 2 < End 2 <= max(id)\nYou can click Remake.\n")
        return False
def input_start2():
    global csv, start1, end1, start2, end2
    global text_result, entry_start2, frame_right_2_left, button_save, button_integrate
    # check
    End2 = end2.get()
    Start2 = start2.get()
    End1 = end1.get()
    Start1 = start1.get()
    if Start1.isdigit() and End1.isdigit() and Start2.isdigit() and End2.isdigit():
        End2 = int(End2)
        Start2 = int(Start2)
        End1 = int(End1)
        Start1 = int(Start1)
    else:
        return False
    """
    # IntVar() can't be upgraded, show warning in the plot instead.
    if Start2 <= End1:
        start2.set(End1 + 1)
        entry_start2 = Spinbox(frame_right_2_left, textvariable = start2, validate = "all", validatecommand = input_start2, from_ = end1.get() + 1, to = end2.get() - 1, increment = 1)
        entry_start2.pack(side = LEFT, fill = BOTH, expand = TRUE)
        return False
    elif Start2 >= End2:
        start2.set(End2 - 1)
        entry_start2 = Spinbox(frame_right_2_left, textvariable = start2, validate = "all", validatecommand = input_start2, from_ = end1.get() + 1, to = end2.get() - 1, increment = 1)
        entry_start2.pack(side = LEFT, fill = BOTH, expand = TRUE)
        return False
    """
    if Start2 > End1 and Start2 < End2:
        calculate_regression()
        button_save.config(state = NORMAL)
        button_integrate.config(state = NORMAL)
        return True
    else:
        # invalid value
        wrong_plot(csv, Start1, End1, Start2, End2)
        text_result.config(state = NORMAL)
        text_result.delete('1.0', '7.0')
        text_result.insert('1.0', "Required: 0 <= Start 1 < End 1 < Start 2 < End 2 <= max(id)\n")
        text_result.insert('2.0', "You can click Remake.\n")
        text_result.config(state = DISABLED)
        button_save.config(state = DISABLED)
        button_integrate.config(state = DISABLED)
        showinfo(title = "Warning", message = "Required: 0 <= Start 1 < End 1 < Start 2 < End 2 <= max(id)\nYou can click Remake.\n")
        return False
def input_end2():
    global csv, start1, end1, start2, end2, len_csv
    global text_result, entry_end2, frame_right_2_middle, button_save, button_integrate
    # check
    End2 = end2.get()
    Start2 = start2.get()
    End1 = end1.get()
    Start1 = start1.get()
    if Start1.isdigit() and End1.isdigit() and Start2.isdigit() and End2.isdigit():
        End2 = int(End2)
        Start2 = int(Start2)
        End1 = int(End1)
        Start1 = int(Start1)
    else:
        return False
    """
    # IntVar() can't be upgraded, show warning in the plot instead.
    if End2 <= Start2:
        end2.set(Start2 + 1)
        entry_end2 = Spinbox(frame_right_2_middle, textvariable = end2, validate = "all", validatecommand = input_end2, from_ = start2.get() + 1, to = len_csv - 1, increment = 1)
        entry_end2.pack(side = LEFT, fill = BOTH, expand = TRUE)
        return False
    elif End2 >= len_csv:
        end2.set(len_csv - 1)
        entry_end2 = Spinbox(frame_right_2_middle, textvariable = end2, validate = "all", validatecommand = input_end2, from_ = start2.get() + 1, to = len_csv - 1, increment = 1)
        entry_end2.pack(side = LEFT, fill = BOTH, expand = TRUE)
        return False
    """
    if End2 > Start2 and End2 < len_csv:
        calculate_regression()
        button_save.config(state = NORMAL)
        button_integrate.config(state = NORMAL)
        return True
    else:
        # invalid value
        wrong_plot(csv, Start1, End1, Start2, End2)
        text_result.config(state = NORMAL)
        text_result.delete('1.0', '7.0')
        text_result.insert('1.0', "Required: 0 <= Start 1 < End 1 < Start 2 < End 2 <= max(id)\n")
        text_result.insert('2.0', "You can click Remake.\n")
        text_result.config(state = DISABLED)
        button_save.config(state = DISABLED)
        button_integrate.config(state = DISABLED)
        showinfo(title = "Warning", message = "Required: 0 <= Start 1 < End 1 < Start 2 < End 2 <= max(id)\nYou can click Remake.\n")
        return False

def linear(x, k, b):
    return k * x + b
def linear_regression(csv, Start, End):
    End += 1
    x = csv[Start : End, 0]
    y = csv[Start : End, 1]
    k, b = optimize.curve_fit(linear, x, y)[0]
    Sxx = np.sum(np.power(x, 2)) - np.sum(x) ** 2 / (End - Start)
    Syy = np.sum(np.power(y, 2)) - np.sum(y) ** 2 / (End - Start)
    sr = np.sqrt((Syy - k ** 2 * Sxx) / (End - Start - 2))
    stddev_k = np.sqrt(sr ** 2 / Sxx)
    stddev_b = sr * np.sqrt(1 / ((End - Start) - np.sum(x) ** 2 / np.sum(np.power(x, 2))))
    r_square = np.sum(np.power((x * k + b - np.mean(y)), 2)) / Syy
    result = [k, b, stddev_k, stddev_b, r_square, Sxx, Syy, sr]
    return result

def integrate(x, y, k, b, dx):
    S = abs((y - k * x - b) * dx - k * dx * dx * 0.5)
    return S
def Reynolds(csv, Start1, End1, Start2, End2, dx = 0.005):
    # linear regression, get lines
    k1, b1 = linear_regression(csv, Start1, End1)[0 : 2]
    k2, b2 = linear_regression(csv, Start2, End2)[0 : 2]
    # get curve
    x_csv = csv[End1 : (Start2 + 1), 0]
    y_csv = csv[End1 : (Start2 + 1), 1]
    smooth = interpolate.interp1d(x_csv, y_csv, kind = 'cubic')
    x_smooth = np.arange(x_csv[0], x_csv[-1], dx)
    y_smooth = smooth(x_smooth)
    len_smooth = x_smooth.size
    # integrate
    S = [[], []]
    # find equal point
    for i in range(len_smooth):
        S[0].append(integrate(x_smooth[i], y_smooth[i], k1, b1, dx))
        S[1].append(integrate(x_smooth[i], y_smooth[i], k2, b2, dx))
    S1 = 0
    S2 = sum(S[1])
    equalpoint = 0
    for i in range(len_smooth):
        S1 += S[0][i]
        S2 -= S[1][i]
        if S1 >= S2:
            equalpoint = i
            break
    x0 = x_smooth[equalpoint]
    result = [x0, S1, S2]
    return result

def wrong_plot(csv, Start1, End1, Start2, End2, dx = 0.05):
    global P, f, canvas_Reynolds
    # clear figure
    f.clear()
    # scatter
    f.scatter(csv[:, 0], csv[:, 1], s = 25, marker = '+', color = 'dimgray', label = "$\Delta T$ - $t$ data")
    f.scatter(csv[Start1, 0], csv[Start1, 1], s = 15, color = 'darkorange', label = "linear fit 1 endpoints")
    f.scatter(csv[End1, 0], csv[End1, 1], s = 15, color = 'darkorange')
    f.scatter(csv[Start2, 0], csv[Start2, 1], s = 15, color = 'limegreen', label = "linear fit 2 endpoints")
    f.scatter(csv[End2, 0], csv[End2, 1], s = 15, color = 'limegreen')
    # smooth curve
    smooth = interpolate.interp1d(csv[:, 0], csv[:, 1], kind = 'cubic')
    x_curve = np.arange(csv[0, 0], csv[-1, 0], dx)
    y_curve = smooth(x_curve)
    f.plot(x_curve, y_curve, linewidth = 1, color = '#1F77B4', label = "$\Delta T$ - $t$ curve")
    # other plot settings
    f.set_xlabel("$t$ (s)")
    f.set_ylabel("$\Delta T$ (K)")
    f.text(np.max(csv, 0)[0] * 0.2 + np.min(csv, 0)[0] * 0.8, np.max(csv, 0)[1] * 0.5 + np.min(csv, 0)[1] * 0.5, s = "Required: 0 <= Start 1 < End 1 < Start 2 < End 2 <= max(id)\nYou can click Remake.\n", color = 'red')     # remove first # to display warning
    f.legend()
    canvas_Reynolds.draw()
    return
def dynamic_plot(csv, Start1, End1, Start2, End2, k1, b1, k2, b2, dx = 0.05):
    global P, f, canvas_Reynolds
    # clear figure
    f.clear()
    # scatter
    f.scatter(csv[:, 0], csv[:, 1], s = 25, marker = '+', color = 'dimgray', label = "$\Delta T$ - $t$ data")
    f.scatter(csv[Start1, 0], csv[Start1, 1], s = 15, color = 'darkorange', label = "linear fit 1 endpoints")
    f.scatter(csv[End1, 0], csv[End1, 1], s = 15, color = 'darkorange')
    f.scatter(csv[Start2, 0], csv[Start2, 1], s = 15, color = 'limegreen', label = "linear fit 2 endpoints")
    f.scatter(csv[End2, 0], csv[End2, 1], s = 15, color = 'limegreen')
    # smooth curve
    smooth = interpolate.interp1d(csv[:, 0], csv[:, 1], kind = 'cubic')
    x_curve = np.arange(csv[0, 0], csv[-1, 0], dx)
    y_curve = smooth(x_curve)
    f.plot(x_curve, y_curve, linewidth = 1, color = '#1F77B4', label = "$\Delta T$ - $t$ curve")
    # linear fit
    y1 = k1 * x_curve + b1
    y2 = k2 * x_curve + b2
    f.plot(x_curve, y1, ls = "--", linewidth = 1, color = 'darkorange', label = "linear fit 1")
    f.plot(x_curve, y2, ls = "--", linewidth = 1, color = 'limegreen', label = "linear fit 2")
    # other plot settings
    f.set_xlabel("$t$ (s)")
    f.set_ylabel("$\Delta T$ (K)")
    f.legend()
    canvas_Reynolds.draw()
    return
def Reynolds_plot(csv, Start1, End1, Start2, End2, k1, b1, k2, b2, x0, dx = 0.05):
    global P, f, canvas_Reynolds
    # clear figure
    f.clear()
    # scatter
    f.scatter(csv[Start1, 0], csv[Start1, 1], s = 15, color = 'darkorange', label = "linear fit 1 endpoints")
    f.scatter(csv[End1, 0], csv[End1, 1], s = 15, color = 'darkorange')
    f.scatter(csv[Start2, 0], csv[Start2, 1], s = 15, color = 'limegreen', label = "linear fit 2 endpoints")
    f.scatter(csv[End2, 0], csv[End2, 1], s = 15, color = 'limegreen')
    f.scatter(csv[:, 0], csv[:, 1], s = 25, marker = '+', color = 'dimgray', label = "$\Delta T$ - $t$ data")
    # smooth curve
    smooth = interpolate.interp1d(csv[:, 0], csv[:, 1], kind = 'cubic')
    x_curve = np.arange(csv[0, 0], csv[-1, 0], dx)
    y_curve = smooth(x_curve)
    f.plot(x_curve, y_curve, linewidth = 1, color = '#1F77B4', label = "$\Delta T$ - $t$ curve")
    # linear fit
    y1 = k1 * x_curve + b1
    y2 = k2 * x_curve + b2
    f.plot(x_curve, y1, ls = "--", linewidth = 1, color = 'darkorange', label = "linear fit 1")
    f.plot(x_curve, y2, ls = "--", linewidth = 1, color = 'limegreen', label = "linear fit 2")
    # Reynolds line
    T1 = k1 * x0 + b1
    T2 = k2 * x0 + b2
    if T1 > T2:
        T1, T2 = T2, T1
    dT = T2 - T1
    y3 = np.arange(T1 - dT * 0.1, T2 + dT * 0.1, dx)
    x3 = np.full(len(y3), x0)
    f.plot(x3, y3, ls = "--", color = 'red', linewidth = 1, label = "Reynolds auxiliary line")
    # integrate area
    smooth = interpolate.interp1d(csv[:, 0], csv[:, 1], kind = 'cubic')
    x_area1 = np.arange(csv[End1, 0], x0, dx)  # use if csv is not reversed in main()
    x_area2 = np.arange(x0, csv[Start2, 0], dx)    # use if csv is not reversed in main()
    y_area1_linear = k1 * x_area1 + b1
    y_area2_linear = k2 * x_area2 + b2
    y_area1_smooth = smooth(x_area1)
    y_area2_smooth = smooth(x_area2)
    f.fill_between(x_area1, y_area1_linear, y_area1_smooth, color = 'grey', alpha = 0.2)
    f.fill_between(x_area2, y_area2_linear, y_area2_smooth, color = 'grey', alpha = 0.2)
    # other plot settings
    f.set_xlabel("$t$ (s)")
    f.set_ylabel("$\Delta T$ (K)")
    f.legend()
    canvas_Reynolds.draw()
    return

def terminate():
    root.destroy()

def main():
    global path, csv, start1, end1, start2, end2, len_csv
    # generate root window
    global root
    root = Tk()
    root.title("Reynolds Correction")
    # high DPI settings
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    root.tk.call('tk', 'scaling', ScaleFactor / 75)
    # set variables
    start1 = StringVar(master = root)
    end1 = StringVar(master = root)
    start2 = StringVar(master = root)
    end2 = StringVar(master = root)
    end2.set("3")
    start2.set("2")
    end1.set("1")
    start1.set("0")
    # root/frame_left
    frame_left = Frame(root, borderwidth = 5, relief = RIDGE)
    frame_left.pack(side = LEFT, fill = BOTH, expand = YES)
    # root/frame_left/frame_left_1
    frame_left_1 = Frame(frame_left, borderwidth = 2)
    frame_left_1.pack(fill = BOTH)
    # root/frame_left/frame_left_1/button_file
    button_file = Button(frame_left_1, text = "File (*.csv, *.txt)", command = openfile, height = 2, width = 20)
    button_file.pack(fill = BOTH)
    # root/frame_left/frame_left_2
    frame_left_2 = Frame(frame_left, borderwidth = 2)
    frame_left_2.pack(fill = BOTH)
    # root/frame_left/frame_left_2/button_save
    global button_save
    button_save = Button(frame_left_2, text = 'Save (*.png)', command = savefile, height = 2, width = 20)
    button_save.config(state = DISABLED)
    button_save.pack(fill = BOTH)
    # root/frame_left/frame_left_3
    global frame_left_3
    frame_left_3 = Frame(frame_left, borderwidth = 5)
    frame_left_3.pack(fill = BOTH, expand = TRUE)
    # root/frame_left/frame_left_3/frame_left_3_1
    frame_left_3_1 = Frame(frame_left_3)
    frame_left_3_1.pack(fill = BOTH, expand = TRUE)
    # root/frame_left/frame_left_3/frame_left_3_1/scrollbar_csv
    scrollbar_csv = Scrollbar(frame_left_3_1)
    scrollbar_csv.pack(side = RIGHT, fill = Y)
    # root/frame_left/frame_left_3/frame_left_3_1/listbox_csv
    global listbox_csv
    listbox_csv = Listbox(frame_left_3_1, yscrollcommand = scrollbar_csv.set, selectmode = EXTENDED)
    listbox_csv.pack(side = LEFT, fill = BOTH, expand = TRUE)
    scrollbar_csv.config(command = listbox_csv.yview)
    # root/frame_left/frame_left_3/label_path
    global label_path
    label_path = Label(frame_left_3, text = path, height = 2)
    label_path.pack(fill = BOTH)

    # root/frame_right
    frame_right = Frame(root, borderwidth = 5, relief = RIDGE)
    frame_right.pack(side = RIGHT, fill = BOTH, expand = YES)
    # root/frame_right/frame_right_1
    frame_right_1 = Frame(frame_right, borderwidth = 2)
    frame_right_1.pack(fill = BOTH)
    # root/frame_right/frame_right_1/frame_right_1_left
    global frame_right_1_left
    frame_right_1_left = Frame(frame_right_1, padx = 30, pady = 10)
    frame_right_1_left.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_1/frame_right_1_left/label_start1
    label_start1 = Label(frame_right_1_left, text = "Start 1", padx = 10)
    label_start1.pack(side = LEFT, fill = BOTH)
    # root/frame_right/frame_right_1/frame_right_1_left/entry_start1
    global entry_start1
    entry_start1 = Spinbox(frame_right_1_left, textvariable = start1, command = input_start1, from_ = 0, to = len_csv - 1, increment = 1)
    entry_start1.config(state = DISABLED)
    entry_start1.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_1/frame_right_1_middle
    global frame_right_1_middle
    frame_right_1_middle = Frame(frame_right_1, padx = 30, pady = 10)
    frame_right_1_middle.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_1/frame_right_1_middle/label_end1
    label_end1 = Label(frame_right_1_middle, text = "End 1", padx = 10)
    label_end1.pack(side = LEFT, fill = BOTH)
    # root/frame_right/frame_right_1/frame_right_1_middle/entry_end1
    global entry_end1
    entry_end1 = Spinbox(frame_right_1_middle, textvariable = end1, command = input_end1, from_ = 0, to = len_csv - 1, increment = 1)
    entry_end1.config(state = DISABLED)
    entry_end1.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_1/frame_right_1_right
    frame_right_1_right = Frame(frame_right_1)
    frame_right_1_right.pack(side = LEFT, fill = BOTH)
    # root/frame_right/frame_right_1/frame_right_1_right/button_integrate
    global button_remake
    button_remake = Button(frame_right_1_right, text = "Remake", command = remakefile, height = 2, width = 20)
    button_remake.config(state = DISABLED)
    button_remake.pack(fill = BOTH)
    # root/frame_right/frame_right_2
    frame_right_2 = Frame(frame_right, borderwidth = 2)
    frame_right_2.pack(fill = BOTH)
    # root/frame_right/frame_right_2/frame_right_2_left
    global frame_right_2_left
    frame_right_2_left = Frame(frame_right_2, padx = 30, pady = 10)
    frame_right_2_left.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_2/frame_right_2_left/label_start2
    label_start2 = Label(frame_right_2_left, text = "Start 2", padx = 10)
    label_start2.pack(side = LEFT, fill = BOTH)
    # root/frame_right/frame_right_2/frame_right_2_left/entry_start2
    global entry_start2
    entry_start2 = Spinbox(frame_right_2_left, textvariable = start2, command = input_start2, from_ = 0, to = len_csv - 1, increment = 1)
    entry_start2.config(state = DISABLED)
    entry_start2.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_2/frame_right_2_middle
    global frame_right_2_middle
    frame_right_2_middle = Frame(frame_right_2, padx = 30, pady = 10)
    frame_right_2_middle.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_2/frame_right_2_middle/label_end2
    label_end2 = Label(frame_right_2_middle, text = "End 2", padx = 10)
    label_end2.pack(side = LEFT, fill = BOTH)
    # root/frame_right/frame_right_2/frame_right_2_middle/entry_end2
    global entry_end2
    entry_end2 = Spinbox(frame_right_2_middle, textvariable = end2, command = input_end2, from_ = 0, to = len_csv - 1, increment = 1)
    entry_end2.config(state = DISABLED)
    entry_end2.pack(side = LEFT, fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_2/frame_right_1_right
    frame_right_2_right = Frame(frame_right_2)
    frame_right_2_right.pack(side = LEFT, fill = BOTH)
    # root/frame_right/frame_right_2/frame_right_1_right/button_integrate
    global button_integrate
    button_integrate = Button(frame_right_2_right, text = "Integrate", command = calculate_integrate, height = 2, width = 20)
    button_integrate.config(state = DISABLED)
    button_integrate.pack()
    # root/frame_right/frame_right_3
    frame_right_3 = Frame(frame_right, borderwidth = 5, relief = SUNKEN)
    frame_right_3.pack(fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_3/text_result
    global text_result
    text_result = Text(frame_right_3, height = 7, wrap = CHAR, padx = 8, pady = 8)
    text_result.insert('1.0', "使用说明\n")
    text_result.insert('2.0', "1. 点击File导入文件。\n")
    text_result.insert('3.0', "2. csv或txt文件格式：两列纯数据，第一列为升序的time(s)，第二列Delta_T(K)；同一行数据间以半角逗号分隔。\n")
    text_result.insert('4.0', "3. 调整Start 1 < End 1 < Start 2 < End 2至合适位置，推荐单击输入栏后使用键盘↑↓进行调节，报错可以Remake。\n")
    text_result.insert('5.0', "4. 点击Integrate积分。\n")
    text_result.insert('6.0', "5. 点击Save按钮保存png格式图片，与数据文件位于同一目录。也可使用下方matplotlib控件，若显示不全请调整窗口大小。\n")
    text_result.config(state = DISABLED)
    text_result.pack(fill = BOTH)
    # root/frame_right/frame_right_4
    frame_right_4 = Frame(frame_right, borderwidth = 5, relief = SUNKEN)
    frame_right_4.pack(fill = BOTH, expand = TRUE)
    # root/frame_right/frame_right_4/canvas_Reynolds
    global P, canvas_Reynolds
    canvas_Reynolds = FigureCanvasTkAgg(P, master = frame_right_4)
    canvas_Reynolds.draw()
    canvas_Reynolds.get_tk_widget().pack(fill = BOTH, expand = TRUE)
    toolbar = NavigationToolbar2Tk(canvas_Reynolds, frame_right_4)
    toolbar.update()
    root.protocol("WM_DELETE_WINDOW", terminate)
    root.mainloop()

main()