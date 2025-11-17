# Розширення функціоналу префіксного дерева Trie
# 
# Пояснення реалізації:
#   - has_prefix(prefix): проходжу символи префікса; якщо шлях існує — повертаю True,
#      якщо поточний вузол вже завершує слово, або якщо в піддереві є хоча б одне термінальне слово.
#   - count_words_with_suffix(pattern): один глибинний обхід усього дерева; тримаю ковзне вікно останніх k=len(pattern) символів 
#       у deque(maxlen=k) та інкрементую лічильник кожного разу, коли зустрічаю кінець слова і вікно дорівнює pattern. 
#       Так не будуються всі рядки цілком і не колекціонуються всі ключі, що краще для великих наборів.


from collections import deque
from trie import Trie


class Homework(Trie):
    def count_words_with_suffix(self, pattern) -> int:
        """
        Повертає кількість слів у Trie, що закінчуються на pattern.
        - Враховує регістр.
        - Якщо pattern == "", повертає загальну кількість слів.
        Реалізація: один DFS по дереву з ковзним вікном останніх k символів.
        """
        if not isinstance(pattern, str):
            raise TypeError("pattern must be a string")

        if pattern == "":
            return self.size  # порожній суфікс підходить будь-якому слову

        k = len(pattern)
        target = pattern
        cnt = 0
        window = deque(maxlen=k)  # автоматично викидає зліва, коли довжина > k

        def dfs(node):
            nonlocal cnt
            # Якщо це кінець слова — перевіряємо, чи вікно дорівнює суфіксу
            if node.value is not None and len(window) == k and "".join(window) == target:
                cnt += 1
            # Обхід дітей
            for ch, nxt in node.children.items():
                before = len(window)
                window.append(ch)
                dfs(nxt)
                # Відкочуємо лише те, що додали на цьому рівні
                if len(window) > before:
                    window.pop()

        dfs(self.root)
        return cnt

    def has_prefix(self, prefix) -> bool:
        """
        True, якщо існує хоч одне слово з префіксом prefix; інакше False.
        Кроки: йдемо по символах; якщо шлях є — перевіряємо, чи поточний вузол
        вже кінець слова або в піддереві існує термінальний вузол.
        """
        if not isinstance(prefix, str):
            raise TypeError("prefix must be a string")

        cur = self.root
        for ch in prefix:
            if ch not in cur.children:
                return False
            cur = cur.children[ch]

        if cur.value is not None:
            return True

        # шукаємо будь-який термінальний вузол у піддереві
        stack = [cur]
        while stack:
            node = stack.pop()
            if node.value is not None:
                return True
            stack.extend(node.children.values())
        return False


if __name__ == "__main__":
    trie = Homework()
    words = ["apple", "application", "banana", "cat"]
    for i, word in enumerate(words):
        trie.put(word, i)

    # Перевірка кількості слів, що закінчуються на заданий суфікс
    assert trie.count_words_with_suffix("e") == 1  # apple
    assert trie.count_words_with_suffix("ion") == 1  # application
    assert trie.count_words_with_suffix("a") == 1  # banana
    assert trie.count_words_with_suffix("at") == 1  # cat

    # Перевірка наявності префікса
    assert trie.has_prefix("app") is True  # apple, application
    assert trie.has_prefix("bat") is False
    assert trie.has_prefix("ban") is True  # banana
    assert trie.has_prefix("ca") is True  # cat

    print("All checks passed.")
