import progressbar

from itertools import cycle
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import rcParams
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_pdf import PdfPages

from helper import chunks, fill_data


class BatchPlotter:
    def __init__(self, contract, database):
        self.contract = contract

        self.database = database
        self.tx_collection = database['transactions']
        self.txreceipt_collection = database['txreceipts']

    def plot(self, start_block, end_block, output, batch_size=20):

        # Create a colour code cycler e.g. 'C0', 'C1', etc.
        n_functions = len(self.contract.all_functions())
        color_codes = map('C{}'.format, cycle(range(max(10, n_functions))))

        batch_chunks = chunks(range(start_block, end_block+1), batch_size)
        batch_chunks = [list(i) for i in batch_chunks]

        if len(batch_chunks) > 1 and len(batch_chunks[-1]) == 1:
            batch_chunks[-2] += batch_chunks[-1]
            del batch_chunks[-1]

        pdf_file = PdfPages(output)
        plot_style_dict = {}

        bar = progressbar.ProgressBar(max_value=end_block-start_block)

        for batch in batch_chunks:
            batch_dict = {}

            figure = plt.figure()

            ax = figure.gca()
            ax.set_xticks(batch)
            ax.set_xticklabels([str(i) for i in batch])

            for label in ax.get_xmajorticklabels():
                label.set_rotation(30)
                label.set_horizontalalignment("right")

            ax.set_xlim((min(batch)-0.5, max(batch)+0.5))

            ax.set_title('Fn calls for contract\n%s\nin blocks %d to %d'%(self.contract.address, batch[0], batch[-1]))

            for block_number in batch:
                bar.update(block_number-start_block)

                block_dict = self.get_block_dict(block_number)

                for item_name, item_count in block_dict.items():
                    if not item_name in batch_dict:
                        batch_dict[item_name] = {}

                    if not block_number in batch_dict[item_name]:
                        batch_dict[item_name][block_number] = 0

                    batch_dict[item_name][block_number] += item_count


                    if not item_name in plot_style_dict:
                        color_code = next(color_codes)
                        plot_style_dict[item_name] = {"color": color_code, "edgecolor":"black"}
                        plot_style_dict[item_name+" {failed}"] = {"color": color_code, "edgecolor":"black", "hatch":"/"}


            bottom = [0 for i in batch]

            for fn_name, call_dict in batch_dict.items():
                pairs = [(k,v) for k,v in call_dict.items()]
                pairs = sorted(pairs, key=lambda item: item[0])
                X = [i[0] for i in pairs]
                Y = [i[1] for i in pairs]

                X, Y = fill_data(X, Y, batch[0], batch[-1])

                ax.bar(X, Y, bottom=bottom, label=fn_name, **plot_style_dict[fn_name])
                ax.legend()

                bottom = [a+b for a,b in zip(bottom, Y)]

            ax.set_axisbelow(True)
            ax.set_ylim(0, max(max(bottom), 10)*1.05)
            ax.set_yticks(list(range(0, max(bottom)+1)))
            ax.grid()

            pdf_file.savefig(figure)

        bar.finish()

        pdf_file.close()


    def get_block_dict(self, block_number):
        raise Exception('Override this')
