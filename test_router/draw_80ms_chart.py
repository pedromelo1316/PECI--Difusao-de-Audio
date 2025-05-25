import ast
import matplotlib.pyplot as plt

def parse_line(line):
    try:
        first_part, dict_part = line.strip().split('sequencial_lost: ', 1)
    except ValueError:
        raise ValueError(f"Line missing 'sequencial_lost:' field: {line}")

    c_str = first_part.split(',')[0]
    c = int(c_str.split(':')[1].strip())

    seq_lost_dict = ast.literal_eval(dict_part.strip())

    return {'c': c, 'sequencial_lost': seq_lost_dict}

def read_data(filename):
    data = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip():
                parsed = parse_line(line)
                data.append(parsed)
    return data

def plot_max_sequential_loss(data):
    channels = [d['c'] for d in data]
    max_seq_loss = [max(d['sequencial_lost'].keys()) for d in data]


    plt.plot(channels, max_seq_loss, marker='o')
    plt.xlabel('Channels (c)')
    plt.ylabel('Max Sequential Packet Loss')
    plt.title('Max Sequential Packet Loss vs Channels')
    plt.grid(True)
    plt.show()

if __name__ == '__main__':
    filename = 'statistics_80ms.txt'
    data = read_data(filename)
    plot_max_sequential_loss(data)
