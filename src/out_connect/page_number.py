class Page:
    def __init__(self, config, x, y):
        x_direction = config.direction[0]
        y_direction = config.direction[1]
        Xo = config.first[0]
        Yo = config.first[1]
        x_size = config.size[0]
        y_size = config.size[1]

        self._page = f"{y_direction * int((y-Yo)/y_size) + 1}"
        self._subpage = f"{x_direction * int((x-Xo)/x_size) + 1}"

    def __repr__(self):
        return f"{self._page}.{self._subpage}"


def page_number(station, x, y):
    return str(Page(station.conf.page_number, x, y))

