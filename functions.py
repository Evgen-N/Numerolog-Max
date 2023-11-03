from datetime import datetime, date
import ast
import json
import numpy as np
from numpy.linalg import eig


def filter_date(input_date):

    d_today_year = date.today().year

    try:
        # преобразуем строку в объект datetime
        bd = datetime.strptime(input_date, '%d.%m.%Y').date()
        if 1900 < bd.year < d_today_year:
            return True
        else:
            return False
    except ValueError:
        # если возникла ошибка ValueError, значит, дата введена некорректно
        return False



def save_clients(user_dict):
    # global clients_for_two
    # clients_for_two = {item: dict(value) for (item, value) in clients_for_two.items()}
    with open("clients_for_two.json", "w", encoding="utf-8") as cli:
        cli.write(json.dumps(user_dict, ensure_ascii=False, indent = 4))
        # print("Список клиентов был успешно сохранен в файле clients_for_two.json.")


def load_clients():
    # global clients_for_two
    with open("clients_for_two.json", "r", encoding="utf-8") as cli:
        user_dict = json.load(cli)
        # clients_for_two = {item: datetime.strptime(value, '%Y-%m-%d').date() for (item, value) in clients_for_two.items()}
        # print("Список клиентов был успешно загружен.")
        return user_dict



def give_predict(arkan_number, predict_number):
    # распечатываем предсказание

    try:
        with open('Sun.txt') as f:
            text = f.read()
        dict_of_predicts = ast.literal_eval(text)
        # for key in dict_of_predicts.keys():
        #     for i in range(len(dict_of_predicts.get(key))):
        #         dict_of_predicts[key][i] = dict_of_predicts.get(key)[i].split("n")
        print("Список прогнозов был успешно загружен.")
    except:
        dict_of_predicts = {}
        print("Список прогнозов не обнаружен. Создан новый пустой список прогнозов.")


    # sents = dict_of_predicts[arkan_number][predict_number]
    # for sent in sents:
    #     print(sent)

    return dict_of_predicts[arkan_number][predict_number]


def calculations(bd_client: str, bd_paar: str) -> int:
    # управляющая функция для формирования матрицы,
    # вычисления её собственных чисел и
    # выражению их по модулю 22

    A = made_matrix(bd_client)
    # print("A = ", A)
    B = made_matrix(bd_paar)
    # print("B = ", B)
    M = np.dot(A + B, np.transpose(A + B))
    lam, vec = eig(M)
    lam = [max(lam), min(lam)]
    # print(lam, max(lam))
    lam[0] = int(lam[0])
    lam[1] = int(lam[1])
    # print(" lambda_1, Lambda_2 = ", lam[0], lam[1])
    # print(" modul_22(lambda_1, Lambda_2) = ", modul_m(lam[0], lam[1], 22))

    number_1, number_2 = modul_m(lam[0], lam[1], 22)
    # print("Ваше сильное число судьбы: ", number_1)
    # print("Ваше слабое число судьбы: ", number_2)
    # print(give_predict(number_1, 0))
    return number_1, number_2


def made_matrix(input_date):
    # собирает матрицу размером 4х2 из даты рожденья

    bdt = datetime.strptime(input_date, '%d.%m.%Y')
    if len(str(bdt.day)) == 1:
        dday = [0, bdt.day]
    else:
        dday = [int(str(bdt.day)[0]), int(str(bdt.day)[1])]
    if len(str(bdt.month)) == 1:
        mmonth = [0, bdt.month]
    else:
        mmonth = [int(str(bdt.month)[0]), int(str(bdt.month)[1])]

    A = [[dday[0], dday[1], mmonth[0], mmonth[1]],
         [int(x) for x in str(bdt.year)]]

    return  np.array(A)


def modul_m(v1, v2, m):
    # Находит значения целых положительных чисел v1 и v2 по модулю m
    while v1 >= m:
        v1 -= m
    while v2 >= m:
        v2 -= m
    return int(v1), int(v2)



