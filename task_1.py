# програма для моделювання мережі потоків для логістики товарів зі складів до магазинів, 
# використовуючи алгоритм максимального потоку. 
# Проведено аналіз отриманих результатів і порівняно їх з теоретичними знаннями.


"""
Програма моделює логістичну мережу «термінали → склади → магазини» і
обчислює максимальний потік за алгоритмом Едмондса–Карпа.

- Побудова графа відповідає структурі зі скрінів (2 термінали, 4 склади, 14 магазинів).
- Розкладка підсумкового потоку по парах «Термінал → Магазин» робиться
  пропорційно внеску кожного термінала у вхід потоку конкретного складу.
- Результати зберігаються у CSV та короткому README.
"""

from __future__ import annotations

from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Dict, Tuple, Iterable, List
import csv


# ---------------------------------------------------------------------------
# Алгоритм максимального потоку (Едмондс–Карп)
# ---------------------------------------------------------------------------

@dataclass
class _PathResult:
    """Результат пошуку доповнювального шляху."""
    bottleneck: int                  # мінімальна залишкова ємність на шляху
    parent: Dict[str, str | None]    # «батько» кожної вершини в BFS-дереві


class MaxFlow:
    """
    Проста реалізація алгоритму Едмондса–Карпа.

    graph[u][v] = C означає орієнтоване ребро u→v з ємністю C.
    Внутрішньо зберігаємо лише прямі ребра (зворотні додаються при ініціалізації
    резидуального графа).
    """

    def __init__(self) -> None:
        # словник словників: вихідні ребра з ємностями
        self.graph: Dict[str, Dict[str, int]] = defaultdict(dict)
        self.nodes: set[str] = set()

    # побудова графа

    def add_edge(self, u: str, v: str, c: int) -> None:
        """
        Додає/накопичує ребро u→v з ємністю c.
        Якщо ребро вже існує — ємність підсумовується (зручно для агрегацій).
        """
        if c < 0:
            raise ValueError("Ємність ребра повинна бути невід'ємною")

        self.nodes.add(u)
        self.nodes.add(v)

        # додається/накопичуться пряма ємність
        self.graph[u][v] = self.graph[u].get(v, 0) + c

        # гарантується наявність запису для v у self.graph (щоб ітерації були простіші)
        self.graph.setdefault(v, self.graph.get(v, {}))

    # обчислення maxflow

    def _build_residual(self) -> Dict[str, Dict[str, int]]:
        """
        Створює резидуальний граф: для кожного прямого ребра u→v з ємністю C
        додаємо:
            - залишкову ємність по прямому ребру:  res[u][v] = C
            - зворотне ребро з нульовою ємністю:  res[v][u] = 0
        """
        res: Dict[str, Dict[str, int]] = {u: dict(vs) for u, vs in self.graph.items()}
        # додаються зворотні ребра з нульовою ємністю там, де їх немає
        for u in list(res.keys()):
            for v in list(res[u].keys()):
                res.setdefault(v, {}).setdefault(u, 0)
        return res

    def _bfs_augment(self, res: Dict[str, Dict[str, int]], s: str, t: str) -> _PathResult | None:
        """
        BFS по резидуальному графу для пошуку доповнювального шляху s→t.
        Повертає _PathResult з «bottleneck» (мінімальна залишкова ємність на шляху).
        Якщо шляху немає — повертає None.
        """
        parent: Dict[str, str | None] = {s: None}
        q: deque[str] = deque([s])

        while q:
            u = q.popleft()
            for v, cap in res[u].items():
                # переходимо лише по позитивній залишковій ємності
                if v not in parent and cap > 0:
                    parent[v] = u
                    if v == t:
                        # знайшли t — одразу відновлюємо «вузьке місце» (bottleneck)
                        bottleneck = float("inf")
                        x = v
                        while parent[x] is not None:
                            p = parent[x]  # тип: ignore
                            bottleneck = min(bottleneck, res[p][x])
                            x = p
                        return _PathResult(int(bottleneck), parent)
                    q.append(v)

        return None

    def edmonds_karp(self, s: str, t: str) -> Tuple[int, Dict[str, Dict[str, int]], Dict[str, Dict[str, int]]]:
        """
        Основний алгоритм: поки існує доповнювальний шлях — збільшуємо потік на його «bottleneck».

        Повертає:
            total_flow        — значення максимального потоку
            flow_matrix[u][v] — фактичний потік, який пройшов по ребру u→v
            residual          — фінальний резидуальний граф (після насичення)
        """
        # 1) створюємо резидуальний граф
        residual = self._build_residual()

        total_flow = 0

        # 2) повторюємо пошук шляху і насичення
        while True:
            res_path = self._bfs_augment(residual, s, t)
            if res_path is None:  # шляхів більше немає — алгоритм завершується
                break

            aug = res_path.bottleneck
            total_flow += aug

            # 3) йдемо назад по батьківському ланцюжку і оновлюємо залишкові ємності
            v = t
            while res_path.parent[v] is not None:
                u = res_path.parent[v]  # тип: ignore
                residual[u][v] -= aug          # витратили ємність на прямому ребрі
                residual[v][u] += aug          # збільшили ємність зворотного ребра
                v = u

        # 4) Відновлюємо матрицю фактичних потоків з різниці «початкова ємність – залишкова»
        flow_matrix: Dict[str, Dict[str, int]] = defaultdict(dict)
        for u in self.graph:
            for v in self.graph[u]:
                cap0 = self.graph[u][v]         # початкова ємність ребра
                cap_res = residual[u][v]        # те, що лишилося в резидуальному
                used = cap0 - cap_res           # отже, стільки «пройшло»
                flow_matrix[u][v] = used if used > 0 else 0

        return total_flow, flow_matrix, residual


# Побудова мережі і запуск розрахунку

def write_readme(max_flow_value: int,
                 terminal_store_flow: Dict[str, Dict[str, float]]) -> None:
    """Сформувати детальний README.md з аналізом та відповідями на питання."""

    # Підсумки за терміналами (з агрегованої таблиці T→M)
    sum_by_terminal = {
        t: round(sum(terminal_store_flow.get(t, {}).values()))
        for t in sorted(terminal_store_flow)
    }
    sums_line = ", ".join(f"{t}={v}" for t, v in sum_by_terminal.items())

    content = (
        "# Логістична мережа: максимальний потік (Едмондс–Карп)\n\n"
        "## Ключові результати\n"
        f"- **Максимальний потік = {max_flow_value}** "
        "(дорівнює сумі вихідних ємностей терміналів: **T1 = 60**, **T2 = 55**).\n"
        "- **Мін-розріз** має пропускну здатність **115** і проходить по ребрах "
        "**SRC→T1 (60)** та **SRC→T2 (55)** — головне вузьке місце.\n"
        "- Ємності **склади→магазини** перевищують вхід на склади, тому склади "
        "**не обмежують** глобальний максимум.\n"
        "- Таблиця фактичних потоків **T→M** збережена у **flows_terminal_store.csv**.\n"
        f"- Підсумок за терміналами: {sums_line}.\n\n"
        "## Модель\n"
        "Вузли: термінали **T1,T2**, склади **S1..S4**, магазини **M1..M14**, "
        "джерело **SRC**, стік **SNK**. Ребра та ємності взято з умови.\n\n"
        "## Алгоритм\n"
        "Використано **Едмондса–Карпа** (BFS у резидуальному графі). "
        "Поки існує доповнювальний шлях `SRC→SNK`, потік збільшується на bottleneck; "
        "залишкові ємності оновлюються. За теоремою мін–макс отриманий потік "
        "дорівнює вазі мінімального розрізу.\n\n"
        "## Інтерпретація (мін–макс)\n"
        "Оскільки **SRC→T1** і **SRC→T2** сумарно дають **115**, а нижні рівні мережі "
        "мають більші сумарні ємності, глобальний максимум дорівнює **115**. "
        "Збільшення ребер **S→M** не змінить максимум, поки не розширені виходи терміналів.\n\n"
        "## Відповіді на контрольні запитання\n"
        "1) Найбільший потік з терміналів: **T1 = 60**, **T2 = 55** — найбільший **T1**.\n"
        "2) Найменші ребра: **S4→M13 (5)**, а також 10-одиничні **S1→M2**, **S2→M5**, "
        "**S3→M9**, **S4→M11**, **S4→M14**. Вони обмежують локальні поставки конкретним "
        "магазинам, але не зменшують глобальний максимум = 115.\n"
        "3) Найменше товарів отримують магазини, підключені до мінімальних ребер: "
        "**M13≈5**, далі **M2/M5/M9/M11/M14≈10** (див. точні значення у CSV). Щоб "
        "збільшити їх постачання, підніміть ємність відповідних **S→M**; якщо мережа "
        "впирається у розріз `SRC→(T1,T2)`, треба підвищити вихід терміналів і/або ребра **T→S**.\n"
        "4) Вузькі місця: головні — **SRC→T1**, **SRC→T2**; також можливі окремі **T→S** "
        "(наприклад, S1 отримує максимум 25, S4 — 30). Усунення: збільшити ємності "
        "**SRC→T*** та/або **T*→S***; за потреби — слабкі ланки **S→M** (особливо **S4→M13**).\n"
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)


def build_and_run() -> int:
    # Спеціальні вершини джерела/стоку (щоб закріпити загальну пропозицію/попит)
    SRC = "SRC"
    SNK = "SNK"

    # Вузли мережі
    terminals = ["T1", "T2"]
    warehouses = ["S1", "S2", "S3", "S4"]
    stores = [f"M{i}" for i in range(1, 15)]

    # Ємності виходу з терміналів у «джерело → термінал».
    # Це еквівалент сумарної пропускної здатності від термінала до складів (із таблиці).
    out_T = {"T1": 25 + 20 + 15, "T2": 15 + 30 + 10}  # = 60 і 55

    # Ребра «термінал → склад» (з таблиці пропускних здатностей)
    edges_T_S = {
        ("T1", "S1"): 25, ("T1", "S2"): 20, ("T1", "S3"): 15,
        ("T2", "S3"): 15, ("T2", "S4"): 30, ("T2", "S2"): 10,
    }

    # Ребра «склад → магазин» (з таблиці пропускних здатностей)
    edges_S_M = {
        ("S1", "M1"): 15, ("S1", "M2"): 10, ("S1", "M3"): 20,
        ("S2", "M4"): 15, ("S2", "M5"): 10, ("S2", "M6"): 25,
        ("S3", "M7"): 20, ("S3", "M8"): 15, ("S3", "M9"): 10,
        ("S4", "M10"): 20, ("S4", "M11"): 10, ("S4", "M12"): 15,
        ("S4", "M13"): 5, ("S4", "M14"): 10,
    }

    # --- Побудова графа ---
    mf = MaxFlow()

    # SRC → термінали (задаємо загальну «пропозицію» кожного термінала)
    for t in terminals:
        mf.add_edge(SRC, t, out_T[t])

    # термінали → склади
    for (t, s), c in edges_T_S.items():
        mf.add_edge(t, s, c)

    # склади → магазини
    for (s, m), c in edges_S_M.items():
        mf.add_edge(s, m, c)

    # магазини → SNK (сток).
    # Якщо для магазину вхідних ребер кілька — сумуємо їх ємності.
    # Якщо магазин взагалі не має вхідних ребер (у нас таких немає) — можна
    # поставити «дуже великий» попит (щоб не обмежувати зверху).
    for m in stores:
        cap_in = sum(c for (s, mm), c in edges_S_M.items() if mm == m)
        mf.add_edge(m, SNK, cap_in if cap_in > 0 else 10**9)

    # --- Розрахунок максимального потоку ---
    max_flow_value, flow_matrix, residual = mf.edmonds_karp(SRC, SNK)

    # -----------------------------------------------------------------------
    # Декомпозиція потоку за парами «Термінал → Магазин»
    # -----------------------------------------------------------------------
    # Ідея: спершу дивимось, скільки фактично кожен термінал загнав у кожен склад,
    # потім пропорційно цьому «розбиваємо» вихід складу на його магазини.

    # 1) Вхід складу з терміналів (фактичні значення з flow_matrix)
    in_T_to_S = defaultdict(lambda: defaultdict(int))  # S -> (T -> flow)
    for (t, s), _ in edges_T_S.items():
        in_T_to_S[s][t] = flow_matrix.get(t, {}).get(s, 0)

    # Сумарний вхід складу (для нормування часток)
    in_total_S = {s: sum(in_T_to_S[s].values()) for s in warehouses}

    # 2) Вихід складу в магазини (фактичний потік)
    out_S_to_M = defaultdict(lambda: defaultdict(int))  # S -> (M -> flow)
    for (s, m), _ in edges_S_M.items():
        out_S_to_M[s][m] = flow_matrix.get(s, {}).get(m, 0)

    # 3) Формуємо таблицю «термінал → магазин» через пропорційний розподіл
    terminal_store_flow = defaultdict(lambda: defaultdict(float))  # T -> (M -> flow)
    for s in warehouses:
        total_in = in_total_S.get(s, 0)
        if total_in == 0:  # склад порожній — пропускаємо
            continue

        # частки внеску терміналів у потік, що увійшов у склад s
        shares = {t: in_T_to_S[s].get(t, 0) / total_in for t in terminals}

        # пропорційно shares розкладаємо потік складу на магазини
        for m, flow_sm in out_S_to_M[s].items():
            if flow_sm == 0:
                continue
            for t, sh in shares.items():
                terminal_store_flow[t][m] += flow_sm * sh

    # -----------------------------------------------------------------------
    # Збереження результатів
    # -----------------------------------------------------------------------
    # CSV з таблицею «Термінал, Магазин, Фактичний потік»
    rows: List[List[object]] = []
    for t, row in terminal_store_flow.items():
        for m, v in row.items():
            if v > 0:
                rows.append([t, m, round(v)])
    rows.sort(key=lambda r: (r[0], int(r[1][1:])))  # групуємо за терміналом, потім M1..M14

    with open("flows_terminal_store.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Термінал", "Магазин", "Фактичний потік (од.)"])
        w.writerows(rows)

    # Генерую README з аналізом
    write_readme(max_flow_value, terminal_store_flow)

    print(f"Максимальний потік: {max_flow_value}")
    return max_flow_value


# Точка входу
if __name__ == "__main__":
    build_and_run()
