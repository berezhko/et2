HEIGHT = 4
from src.elements import Line
from src.elements import Text
from src.elements import AutocadElements

def plot_table(data, table_fromar, offset=(0, 0), align=[]):
    result = []
    height = 0
    width = 0
    for j, row in enumerate(data):
        y = get_line_possition(j)
        y = y + offset[1]
        width = offset[0]
        for i, cell in enumerate(row):
            x, length = get_possition(i, table_fromar)
            x = x + offset[0]
            result = result + plot_border(x, y, length)
            result = result + plot_text(x, y, length, cell, get_align_value(i, align))
            width = width + length
        height = height + HEIGHT
    result += [
        Line((offset[0], offset[1]), (offset[0], offset[1]-height)),
        Line((offset[0], offset[1]-height), (width, offset[1]-height)),
    ]
    return result

def get_align_value(index, align):
    result = 'c'
    if index < len(align):
        result = align[index]
    return result

def get_line_possition(j):
    return -HEIGHT*j

def get_possition(i, table_fromar):
    return sum(table_fromar[:i+1])-table_fromar[i], table_fromar[i]

def plot_border(x, y, length):
    result = [
        Line((x, y), (x + length, y)),
        Line((x + length, y), (x + length, y - HEIGHT)),
    ]
    return result

def plot_text(x, y, length, text, align='c'):
    offset_x = 2
    align_option = ''
    if align == 'c':
        offset_x = length/2
        align_option = "_MC"
    elif align == 'l':
        offset_x = 2
        align_option = "_ML"
    elif align == 'r':
        offset_x = length-2
        align_option = "_MR"
    font_size = HEIGHT/2.0
    return [Text((x + offset_x, y - HEIGHT/2), text, font_size, 0, align_option)]


def plot_split_table(numpy_data, header, table_width, split_rows_first_sheet, split_rows, start_possition, file_name, delta=0, align=[]):
    lisp = get_split_table(
        numpy_data,
        header,
        table_width,
        split_rows_first_sheet,
        split_rows,
        start_possition,
        delta,
        align
    )

    AutocadElements(lisp).save(file_name)
    return lisp

def get_split_table(numpy_data, header, table_width, split_rows_first_sheet, split_rows, start_possition, delta=0, align=[]):
    result = []
    i = 0
    step = start_possition['X']
    import pandas
    offset_for_y = 0
    if header:
        header_table = pandas.DataFrame(header).to_numpy()
        offset_for_y = HEIGHT
    sign = -1 if delta < 0 else +1

    while i < len(numpy_data):
        if i < split_rows_first_sheet: # Считается что на лист входит 2 столбца таблицы
            next = split_rows_first_sheet # Число строк в первом листе
        else:
            next = split_rows
        
        print_table = numpy_data[i:min(i + next, len(numpy_data))]
        if header:
            result += plot_table(header_table, table_width, offset=(step, start_possition['Y']))
        result += plot_table(print_table, table_width, offset=(step, start_possition['Y']-offset_for_y), align=align)
        i = i + next
        step = step + sign*sum(table_width) + delta

    return result


def split_result(a, delim, length):
    """
    Разбиваем строку a на массив строк длинны не более length.
    Если в строке присутствует разделитель delim, то тогда строка разбивается по этому разделителю.
    
    Возвращаемое значение: массив строк
    """
    def output():
        result = (buf, '')
        if delim != '' and buf.rfind(delim) != -1:
            l = buf.rfind(delim)
            result = (buf[:l], buf[l+len(delim):])
        return result

    result = []
    buf = ''
    i = 1
    for c in a:
        buf += c
        if i % length == 0:
            out, buf = output()
            i += len(buf)
            result.append(out)
        i += 1
    result.append(buf)
    return result


def fit_data(plot_arr, table_width, ksize_font=3.0/5, delim=', ', add_blank_line=True):
    """
    Разбиваем таблицу строк plot_arr на таблицу строк, длинна которых меньше чем заданная длинна.
    Заданная длинна расчитавается как средняя ширина шрифта ksize_font умноженное на ширину таблици.
    Таким образом мы вписываем таблицу с текстом в фиксированные размеры, не вылезая за края.
    В дополнении, если строка оказалось длинной и был сделан перенос ее на новую строку в таблице,
    то последующая строка печатается после пропуска пустой (может управляться через параметр 
    add_blank_line).
    """
    result = []
    for row in plot_arr:
        if len(row) != len(table_width):
            raise Exception(len(row), len(table_width), "Error dim!")
        out = []
        max_dim = 0
        for i, el in enumerate(row):
            if type(ksize_font) in (list, tuple):
                k = ksize_font[i]
            else:
                k = ksize_font
            res = split_result(str(el), delim, int(k*table_width[i]))
            out.append(res)
            max_dim = max(max_dim, len(res))
        for i in range(max_dim):
            temp = []
            for el in out:
                if i < len(el):
                    temp.append(el[i])
                else:
                    temp.append('')
            result.append(temp)
        # Добавляем пустую строку, если получилось больше одной строки
        if add_blank_line and max_dim > 1:
            temp = []
            for _ in table_width:
                temp.append('')
            result.append(temp)
    return result