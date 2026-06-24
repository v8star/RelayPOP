import poplib
import ssl


def connect(cfg):

    pop = poplib.POP3_SSL(

        cfg["pop3"]["host"],
        cfg["pop3"]["port"],
        context=ssl.create_default_context()

    )

    pop.user(cfg["pop3"]["username"])
    pop.pass_(cfg["pop3"]["password"])

    return pop


def list_uid(pop):

    _, items, _ = pop.uidl()

    result = []

    for item in items:

        num, uid = item.decode().split()

        result.append(

            (

                int(num),
                uid

            )

        )

    return result


def get_message(pop, number):

    _, lines, _ = pop.retr(number)

    return b"\r\n".join(lines)

def delete_message(pop, number):
    pop.dele(number)


def get_uid_map(pop):

    _, items, _ = pop.uidl()

    mapping = {}

    for item in items:

        num, uid = item.decode().split()

        mapping[uid] = int(num)

    return mapping