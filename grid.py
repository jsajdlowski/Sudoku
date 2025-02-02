from random import sample

def create_line_coordinates(cell_size):
    points=[]
    for y in range(1,9):
        temp=[]
        temp.append((0, y*cell_size))
        temp.append((585, y*cell_size))
        points.append(temp)

    for x in range(1,10):
        temp=[]
        temp.append((x*cell_size,0))
        temp.append((x*cell_size,600))
        points.append(temp)

    # print(points)
    return points

SUB_GRID_SIZE=3
GRID_SIZE=SUB_GRID_SIZE*SUB_GRID_SIZE

def pattern(row_num, col_num):
    return(SUB_GRID_SIZE * (row_num % SUB_GRID_SIZE)+row_num // SUB_GRID_SIZE + col_num) % GRID_SIZE

def shuffle(samp):
    return sample(samp, len(samp))

def create_grid(sub_grid):
    row_base = range(sub_grid)
    rows = [g*sub_grid+r for g in shuffle(row_base) for r in shuffle(row_base)]
    cols = [g*sub_grid+c for g in shuffle(row_base) for c in shuffle(row_base)]
    nums=shuffle(range(1, sub_grid*sub_grid+1))
    return [[nums[pattern(r,c)]for c in cols]for r in rows]


class Grid:
    def __init__(self, font):
        self.cell_size=65
        self.num_x_offset = 22
        self.num_y_offset = 14
        self.line_coordinates = create_line_coordinates(self.cell_size)
        self.grid = create_grid(SUB_GRID_SIZE)
        self.game_font = font

    def draw_lines(self, pg, surface):
        for index, point in enumerate(self.line_coordinates):
            if index==2 or index==5 or index==10 or index==13:
                pg.draw.line(surface, (255,200,0), point[0], point[1])
            else:
                pg.draw.line(surface, (0,50,0), point[0], point[1])

    def draw_numbers(self, surface):
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                if self.get_cell(x,y) != 0:
                    color = (0, 255, 0) if hasattr(self, 'correct_cells') and (x,y) in self.correct_cells else (0, 200, 255)
                    text_surface = self.game_font.render(str(self.get_cell(x,y)), False, color)
                    surface.blit(text_surface, (x*self.cell_size + self.num_x_offset, y*self.cell_size + self.num_y_offset))

    def draw_all(self, pg, surface):
        self.draw_lines(pg, surface)
        self.draw_numbers(surface)

    def get_cell(self, x, y ):
        return self.grid[y][x]
    
    def set_cell(self, x, y, value):
        self.grid[y][x]=value

    def show(self):
        for cell in self.grid:
            print(cell)

    def get_board(self):
        return self.grid
    
    def remove_numbers(self, count):
        self.solution = [row[:] for row in self.grid]

        positions = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)]

        to_remove = sample(positions, count)

        for x, y in to_remove:
            self.grid[y][x] = 0

if __name__ == '__main__':
    grid = Grid()
    grid.show()