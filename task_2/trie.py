# trie.py — базова реалізація Trie

class TrieNode:
    def __init__(self):
        self.children = {}     # char -> TrieNode
        self.value = None      # маркер завершення слова (може зберігати payload)

class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.size = 0          # кількість слів у дереві

    # вставка
    def put(self, key, value=None):
        if not isinstance(key, str) or not key:
            raise TypeError(f"Illegal argument for put: key = {key} must be a non-empty string")
        cur = self.root
        for ch in key:
            if ch not in cur.children:
                cur.children[ch] = TrieNode()
            cur = cur.children[ch]
        if cur.value is None:
            self.size += 1
        cur.value = value

    # пошук точного слова
    def get(self, key):
        if not isinstance(key, str) or not key:
            raise TypeError(f"Illegal argument for get: key = {key} must be a non-empty string")
        cur = self.root
        for ch in key:
            if ch not in cur.children:
                return None
            cur = cur.children[ch]
        return cur.value

    # видалення
    def delete(self, key):
        if not isinstance(key, str) or not key:
            raise TypeError(f"Illegal argument for delete: key = {key} must be a non-empty string")

        def _del(node, k, d):
            if d == len(k):
                if node.value is not None:
                    node.value = None
                    self.size -= 1
                    return len(node.children) == 0
                return False
            ch = k[d]
            if ch in node.children and _del(node.children[ch], k, d + 1):
                del node.children[ch]
                return len(node.children) == 0 and node.value is None
            return False

        _del(self.root, key, 0)

    def is_empty(self):
        return self.size == 0

    # найдовший префікс
    def longest_prefix_of(self, s):
        if not isinstance(s, str) or not s:
            raise TypeError(f"Illegal argument for longestPrefixOf: s = {s} must be a non-empty string")
        cur = self.root
        longest = ""
        cur_pref = ""
        for ch in s:
            if ch in cur.children:
                cur = cur.children[ch]
                cur_pref += ch
                if cur.value is not None:
                    longest = cur_pref
            else:
                break
        return longest

    # всі ключі з префіксом
    def keys_with_prefix(self, prefix):
        if not isinstance(prefix, str):
            raise TypeError(f"Illegal argument for keysWithPrefix: prefix = {prefix} must be a string")
        cur = self.root
        for ch in prefix:
            if ch not in cur.children:
                return []
            cur = cur.children[ch]
        res = []
        self._collect(cur, list(prefix), res)
        return res

    def _collect(self, node, path, out):
        if node.value is not None:
            out.append("".join(path))
        for ch, nxt in node.children.items():
            path.append(ch)
            self._collect(nxt, path, out)
            path.pop()

    # всі ключі
    def keys(self):
        res = []
        self._collect(self.root, [], res)
        return res
