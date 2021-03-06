from traceback import print_tb


class ConsoleMenu:
    """
    A simple console menu allows you to easily implement a basic user interface.
    """

    def __init__(self, title, items: dict, force_exit=False):
        """
        :param title: This title will be displayed
        :param items: pairs of strings and function references
        """
        self.items = items
        self.title = title
        self.__nested = False
        self.force_exit = force_exit

    def __display(self):
        print("\n")
        print(self.title)
        i = 1
        for key in self.items:
            print(str(i) + ") " + str(key))
            i += 1
        print("{}) {}".format(str(i), "back" if self.__nested else "exit"))

    def execute(self):
        while True:
            self.__display()

            try:
                argument = int(input("run: "))
            except (TypeError, ValueError):
                print("Error: Invalid input type")
                continue
            except KeyboardInterrupt:
                break

            if argument not in range(1, len(self.items) + 2):
                print("Error: No such item in menu")
                continue

            if argument == len(self.items) + 1:
                break

            try:
                item = list(self.items.values())[argument - 1]

                if isinstance(item, ConsoleMenu):
                    item.__nested = True
                    item.execute()
                    item.__nested = False
                elif isinstance(item, tuple):
                    func, arg = item
                    it = func(arg)
                    if isinstance(it, ConsoleMenu):
                        it.__nested = True
                        it.execute()
                        it.__nested = False
                    elif it == "back":
                        break
                else:
                    it = item()
                    if isinstance(it, ConsoleMenu):
                        it.__nested = True
                        it.execute()
                        it.__nested = False
                    elif it == "back":
                        break

            except Exception as e:
                print("Error: Failed to run item '{}'".format(list(self.items.keys())[argument - 1]))
                print(str(e))
                print_tb(e.__traceback__)
