from src.station.misc import get_long_cabinet_name
from src.exception import DistanceZero

from src.elements import Line as Line
from src.elements import Text as Text

def make_wires_journal(station, cables_collection, clemmnic_data):
    result = []
    for cable in cables_collection.cables():
        a = {}
        section, type_cab = cables_collection.section(cable)
        count_wires_in_cab = cables_collection.count_wires(cable)
    
        a['Наименование кабеля'] = cable
        a['Тип'] = type_cab
        a['Кол-во и сечение жил'] = count_wires_in_cab+'x'+str(section)
        a['Кол-во исп. жил'] = cables_collection.count_used_wires(cable)
        a['Маркировка используемых жил в кабеле'] = ', '.join(cables_collection.wires(cable))
        a['Примечание'] = ''
        result.append(a)

    preset_cables = station.preset_cables()
    process = []
    for cable in preset_cables.get_marked_cables():
        a = {}
        wires = []
        for row in clemmnic_data:
            if row.cabel == cable:
                if row.process not in process or row.process == 0:
                    wires.append(row.wire)
                    process.append(row.process)
    
        a['Наименование кабеля'] = cable
        a['Тип'] = preset_cables.get_type(cable)
        a['Кол-во и сечение жил'] = preset_cables.get_cores_gauge(cable)
        a['Кол-во исп. жил'] = len(wires)
        a['Маркировка используемых жил в кабеле'] = ', '.join(wires)
        a['Примечание'] = f'({preset_cables.get_notes(cable)})'
        result.append(a)
    return result


def make_cable_journal(station, cables_collection):
    # Сперва добавляем в КЖ новые кабеля
    result = []
    for i, cable in enumerate(cables_collection.cables(), start=1):
        a = {}
        section, type_cab = cables_collection.section(cable)
        count_wires_in_cab = cables_collection.count_wires(cable)
        a['Наименование кабеля'] = cable
        a['Тип'] = type_cab
        a['Жилы'] = count_wires_in_cab +'x'+str(section)
        a['Первая точка'] = get_long_cabinet_name(station, int(cables_collection.get_cabins_by_cable(cable)[0]))
        a['Вторая точка'] = get_long_cabinet_name(station, int(cables_collection.get_cabins_by_cable(cable)[1]))
        a['Длинна'] = str(get_distance(cable, station, cables_collection))
        a['Проложено'] = ''
        a['Монт. ед'] = i
        a['Примечание'] = ''
        result.append(a)
    
    # Добавляем в КЖ старые кабеля с отметкой "Существующий"
    preset_cables = station.preset_cables()
    for i, cable in enumerate(preset_cables.get_marked_cables(), start=len(result)+1):
        a = {}
        a['Наименование кабеля'] = cable
        a['Тип'] = preset_cables.get_type(cable)
        a['Жилы'] = preset_cables.get_cores_gauge(cable)
        a['Первая точка'] = get_long_cabinet_name(station, int(preset_cables.get_cabine1(cable)))
        a['Вторая точка'] = get_long_cabinet_name(station, int(preset_cables.get_cabine2(cable)))
        a['Длинна'] = preset_cables.get_length(cable)
        a['Проложено'] = ''
        a['Монт. ед'] = i
        a['Примечание'] = f'({preset_cables.get_notes(cable)})'
        result.append(a)
    return result


def total_length_journal(station, cables_collection):
    f = lambda x: get_distance(x, station, cables_collection)
    return base_method_for_journal(f, cables_collection)


def count_section_journal(cables_collection):
    return base_method_for_journal(lambda x: 1, cables_collection)


def base_method_for_journal(f, cables_collection):
    result = {}
    for cable in cables_collection.cables():
        section, type_cab = cables_collection.section(cable)
        count_wires_in_cab = cables_collection.count_wires(cable)
        key = type_cab + ' ' + count_wires_in_cab + 'x' + str(section)
        if key not in result:
            result[key] = 0
        result[key] = result[key] + f(cable)
    return result


def get_distance(cable, station, cables_collection):
    direction = cables_collection.cable_to_direction(cable)
    result = 0
    if direction in cables_collection.distance_inside():
        result = round(1.15*cables_collection.distance_inside()[direction] + 0.5)
    if direction in cables_collection.distance_outside():
        result = round(1.05*cables_collection.distance_outside()[direction] + 0.5)
    if result == 0:
        raise DistanceZero(cable, "Distance == 0")
    return result


def shrink_long_string(data, field=1, length=24):
    for row in data:
        if len(row[field]) > length:
            row[field] = f"{row[field][:length-3]}..."
    return data


class CableLinks():
    def __init__(self, station, cables_collection):
        self._station = station
        self._cables_collection = cables_collection
        self.STEP_CABLES = 10
        self.STEP_CLOSETS = 10
        self.MIN_WIDTH_CLOSET = 60
        self.HEIGHT_CLOSET = 40
        self.LENGTH_CABLE = 40
        self.OFFSET_X = 400

    # data = self._cables_collection.make_list_cables_in_closet()
    def remove_special_closet(self, data, exclude_closets):
        list_excluse_cables = []
        for closet in exclude_closets:
            for cable in data[closet]:
                list_excluse_cables.append(cable)
                
        result = {}
        for closet in data:
            if closet in exclude_closets:
                continue
            result[closet] = []
            for cable in data[closet]:
                if cable not in list_excluse_cables:
                    result[closet].append(cable)
            if len(result[closet]) == 0:
                result.pop(closet)
    
        return result
    
    def get_back_closet_list(self, closet):
        result = {}
        cables = self._cables_collection.make_list_cables_in_closet()
        for cable in cables[closet]:
            back_closet = self._cables_collection.get_back_cabin_by_cable(closet, cable)
            if back_closet not in result:
                result[back_closet] = []
            result[back_closet].append(cable)
        return result
    
    def sort_closet_by_count_cables(self, closet_list, reverse=True):
        result = {}
        for closet in sorted(closet_list, key=lambda x: len(closet_list[x]), reverse=reverse):
            result[closet] = closet_list[closet]
        return result
    
    def reverse_cable(self, back_closet_list):
        result = []
        for k in back_closet_list.keys():
            for cable in back_closet_list[k]:
                result.append(cable)
        return list(reversed(result))
    
    def count_cable_in_closet(self, back_closet_list):
        result = 0
        for i in back_closet_list:
            result = result + len(back_closet_list[i])
        return result
    
    def generate_closets_list(self, main_closet):
        back_closet_list = self.sort_closet_by_count_cables(self.get_back_closet_list(main_closet))
        result = {}
        for closet in back_closet_list:
            result[closet] = back_closet_list[closet]
        return result
    
    def calc_closet_location(self, closets, offset_x, offset_y):
        result = {}
        for closet in closets:
            length = self.STEP_CABLES*len(closets[closet])
            if length < self.MIN_WIDTH_CLOSET:
                length = self.MIN_WIDTH_CLOSET
            result[closet] = {'point': (offset_x, offset_y), 'length': length}
            offset_x = offset_x + length + self.STEP_CLOSETS
    
        return result
    
    def calc_cable_location(self, closets, offset_x):
        result = {}
        for closet in closets:
            list_cables_in_closet = closets[closet]
            length = self.STEP_CABLES*len(list_cables_in_closet)
            if length < self.MIN_WIDTH_CLOSET:
                length = self.MIN_WIDTH_CLOSET
            offset_wire = offset_x + self.STEP_CABLES/2
            for cable in list_cables_in_closet:
                if cable not in result:
                    result[cable] = []
                result[cable].append(offset_wire)
                offset_wire = offset_wire + self.STEP_CABLES
            offset_x = offset_x + length + self.STEP_CLOSETS
    
        return result
    
    def plot_closet_frame(self, x0, y0, x1, y1, closet):
        result = [
            Line((x0, y0), (x1, y0)),
            Line((x1, y0), (x1, y1)),
            Line((x1, y1), (x0, y1)),
            Line((x0, y1), (x0, y0)),
        ]
    
        long_all_name = get_long_cabinet_name(self._station, str(int(closet)))
        number_chars = int((x1-x0)/2) - 5
        if len(long_all_name) < number_chars:
            result += [
                Text((x0+2, y0-5), long_all_name, 3, 0)
            ]
        else:
            result += [
                Text((x0+2, y0-5), long_all_name[:number_chars], 3, 0),
                Text((x0+2, y0-10), long_all_name[number_chars:], 3, 0),
            ]
    
        return result
    
    def plot_closets(self, frames_size):
        result = []
        for c in frames_size:
            data = frames_size[c]
            x0 = data['point'][0]
            y0 = data['point'][1]
            x1 = data['point'][0] + data['length']
            y1 = data['point'][1] - self.HEIGHT_CLOSET
            result = result + self.plot_closet_frame(x0, y0, x1, y1, c)
    
        return result
    
    def get_y_position_for_cable(self, frames_size):
        result = 0
        for c in frames_size:
            data = frames_size[c]
            result = data['point'][1] - self.HEIGHT_CLOSET
            break
        return result
    
    def plot_cables(self, cable_position, y):
        result = []
        for cable in cable_position:
            for possition in cable_position[cable]:
                result += [
                    Line((possition, y), (possition, y-self.LENGTH_CABLE)),
                    Text((possition-0.5, y-self.LENGTH_CABLE+5), cable, 2.5, 90),
                ]
        return result
    
    def plot_jumpers(self, cable_position, y):
        from src.out_connect.montage_cable import get_depth_jumpers
        result = []
        for d in get_depth_jumpers(cable_position):
            y1 = y - self.LENGTH_CABLE
            y2 = y1 - 4*int(d)
            for jumper in get_depth_jumpers(cable_position)[d]:
                x1 = jumper[0]
                x2 = jumper[1]
                result += [
                    Line((x1, y1), (x1, y2)),
                    Line((x1, y2), (x2, y2)),
                    Line((x2, y1), (x2, y2)),
                ]
        return result
    
    def get_last_possition_closet(self, dict):
        a = dict[list(dict.keys())[-1]]
        return a['point'][0] + a['length']
    
    def get_first_possition_closet(self, dict):
        a = dict[list(dict.keys())[0]]
        return a['point'][0]
    
    def plot_main_frame(self, frames_size, main_closet, y):
        result = []
        x0 = self.get_first_possition_closet(frames_size)
        x1 = self.get_last_possition_closet(frames_size)
        y0, y1 = y - self.LENGTH_CABLE, y - self.LENGTH_CABLE - self.HEIGHT_CLOSET
        result = result + self.plot_closet_frame(x0, y0, x1, y1, main_closet)
        return result
    
    def plot_closets_with_cables(self, cabinet_size_in_drawing, cable_position, y):
        result = self.plot_closets(cabinet_size_in_drawing)
        return result + self.plot_cables(cable_position, y)
    
    def set_order_closets(self, closets, order):
        result = {}
        for i in order:
            if i in closets:
                result[i] = closets[i]
        for i in closets:
            result[i] = closets[i]
        return result

    def plot_cable_link(self):
        result = []
        offset_x = self.OFFSET_X
        offset_y = 150
        main_closets = self._station.cabine_for_cable_links()
        
        for include_closets in main_closets:
            for main_closet in include_closets:
                closets = self.generate_closets_list(main_closet)
                
                closet_location = self.calc_closet_location(closets, offset_x, offset_y)
                cable_location = self.calc_cable_location(closets, offset_x)
                y = self.get_y_position_for_cable(closet_location)
                result = result + self.plot_closets_with_cables(closet_location, cable_location, y)
                
                result = result + self.plot_main_frame(closet_location, main_closet, y)
                offset_x = self.get_last_possition_closet(closet_location) + 60
            offset_x = self.OFFSET_X
            offset_y = offset_y + 140
        
        #==============================================
        
        offset_x = self.OFFSET_X
        offset_y = 0
        exclude_closets = [closet for l in main_closets for closet in l]
        
        closets = self.remove_special_closet(self._cables_collection.make_list_cables_in_closet(), exclude_closets)
        
        closet_location = self.calc_closet_location(closets, offset_x, offset_y)
        cable_location = self.calc_cable_location(closets, offset_x)
        y = self.get_y_position_for_cable(closet_location)
        result = result + self.plot_closets_with_cables(closet_location, cable_location, y)
        
        result = result + self.plot_jumpers(cable_location, y)
        
        return result