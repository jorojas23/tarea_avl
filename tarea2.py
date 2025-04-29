import json
import difflib
import hashlib
from typing import List, Optional, Dict, Union

# ==================== Módulo 1: Gestión de Branches (Árbol N-ario) ====================
class Commit:
    def __init__(self, id: str, message: str, files: dict):
        self.id = id
        self.message = message
        self.files = files

    def to_dict(self):
        return {
            "id": self.id,
            "message": self.message,
            "files": self.files
        }

class BranchNode:
    def __init__(self, name: str, parent: Optional['BranchNode'] = None):
        self.name = name
        self.parent = parent
        self.children: List[BranchNode] = []
        self.commits: List[Commit] = []

class BranchManager:
    def __init__(self):
        self.root = BranchNode("main")
        self.current = self.root
        self.file = "branches.json"
        self.load()

    def create_branch(self, name: str):
        if any(child.name == name for child in self.current.children):
            raise ValueError(f"Branch {name} already exists")
        new_branch = BranchNode(name, self.current)
        self.current.children.append(new_branch)
        self.save()

    def delete_branch(self, name: str):
        branch = self._find_branch_postorder(self.root, name)
        if branch and not branch.children:
            branch.parent.children.remove(branch)
            self.save()

    def _find_branch_postorder(self, node: BranchNode, name: str) -> Optional[BranchNode]:
        for child in node.children:
            result = self._find_branch_postorder(child, name)
            if result:
                return result
        if node.name == name:
            return node
        return None

    def list_branches_preorder(self):
        self._list_preorder(self.root)

    def _list_preorder(self, node: BranchNode, level: int = 0):
        print("  " * level + node.name)
        for child in node.children:
            self._list_preorder(child, level + 1)

    def checkout(self, name: str) -> bool:
        found = self._checkout_inorder(self.root, name)
        if found:
            self.save()
        return found

    def _checkout_inorder(self, node: BranchNode, name: str) -> bool:
        if node.name == name:
            self.current = node
            return True
        
        for i, child in enumerate(node.children):
            if i < len(node.children) - 1:
                if self._checkout_inorder(child, name):
                    return True
        
        if node.children:
            return self._checkout_inorder(node.children[-1], name)
        
        return False

    def merge(self, source_name: str):
        source = self._find_branch_postorder(self.root, source_name)
        if not source:
            raise ValueError("Source branch not found")
        
        diff = self._calculate_diff(source, self.current)
        self._apply_merge(diff)
        merge_commit = Commit(
            id=hashlib.sha1(str(diff).encode()).hexdigest()[:7],
            message=f"Merge {source_name} into {self.current.name}",
            files=diff
        )
        self.current.commits.append(merge_commit)
        self.save()

    def _calculate_diff(self, source: BranchNode, target: BranchNode) -> dict:
        source_files = {}
        if source.commits:
            source_files = source.commits[-1].files
        
        target_files = {}
        if target.commits:
            target_files = target.commits[-1].files
        
        diff = {}
        for file in set(source_files) | set(target_files):
            if source_files.get(file) != target_files.get(file):
                diff[file] = source_files.get(file) or target_files.get(file)
        return diff

    def _apply_merge(self, diff: dict):
        if self.current.commits:
            current_files = self.current.commits[-1].files.copy()
        else:
            current_files = {}
        
        current_files.update(diff)
        new_commit = Commit(
            id=hashlib.sha1(str(current_files).encode()).hexdigest()[:7],
            message="Merge commit",
            files=current_files
        )
        self.current.commits.append(new_commit)

    # Serialización/Deserialización
    def save(self):
        data = self._serialize(self.root)
        with open(self.file, 'w') as f:
            json.dump(data, f)

    def load(self):
        try:
            with open(self.file, 'r') as f:
                data = json.load(f)
                self.root = self._deserialize(data)
                self.current = self.root
        except FileNotFoundError:
            pass

    def _serialize(self, node: BranchNode) -> dict:
        return {
            "name": node.name,
            "commits": [c.to_dict() for c in node.commits],
            "children": [self._serialize(child) for child in node.children]
        }

    def _deserialize(self, data: dict) -> BranchNode:
        node = BranchNode(data["name"])
        node.commits = [Commit(**c) for c in data["commits"]]
        node.children = [self._deserialize(child) for child in data["children"]]
        return node
    
    def get_current_branch(self) -> str:
        return self.current.name

# ==================== Módulo 2: Administración de Colaboradores (BST) ====================
class Collaborator:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.left = None
        self.right = None

    def to_dict(self):
        return {
            "name": self.name,
            "role": self.role,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None
        }

    @staticmethod
    def from_dict(data: dict) -> Optional['Collaborator']:
        if not data:
            return None
        node = Collaborator(data["name"], data["role"])
        node.left = Collaborator.from_dict(data["left"])
        node.right = Collaborator.from_dict(data["right"])
        return node

class CollaboratorBST:
    def __init__(self):
        self.root: Optional[Collaborator] = None
        self.file = "collaborators.json"
        self.load()

    def add(self, name: str, role: str):
        if not self.root:
            self.root = Collaborator(name, role)
        else:
            self._insert(self.root, name, role)
        self.save()

    def _insert(self, node: Collaborator, name: str, role: str):
        if name < node.name:
            if node.left:
                self._insert(node.left, name, role)
            else:
                node.left = Collaborator(name, role)
        else:
            if node.right:
                self._insert(node.right, name, role)
            else:
                node.right = Collaborator(name, role)

    def remove(self, name: str):
        self.root = self._remove_node(self.root, name)
        self.save()

    def _remove_node(self, node: Optional[Collaborator], name: str) -> Optional[Collaborator]:
        if not node:
            return node

        if name < node.name:
            node.left = self._remove_node(node.left, name)
        elif name > node.name:
            node.right = self._remove_node(node.right, name)
        else:
            if not node.left:
                return node.right
            elif not node.right:
                return node.left

            temp = self._min_value_node(node.right)
            node.name = temp.name
            node.role = temp.role
            node.right = self._remove_node(node.right, temp.name)

        return node

    def _min_value_node(self, node: Collaborator) -> Collaborator:
        current = node
        while current.left:
            current = current.left
        return current

    def find(self, name: str) -> Optional[Collaborator]:
        return self._find_node(self.root, name)

    def _find_node(self, node: Optional[Collaborator], name: str) -> Optional[Collaborator]:
        if not node:
            return None
        if node.name == name:
            return node
        if name < node.name:
            return self._find_node(node.left, name)
        return self._find_node(node.right, name)

    def list_preorder(self):
        print("=== Colaboradores ===")
        self._preorder_traversal(self.root)
        print("====================")

    def _preorder_traversal(self, node: Optional[Collaborator]):
        if node:
            print(f"- {node.name} ({node.role})")
            self._preorder_traversal(node.left)
            self._preorder_traversal(node.right)

    def save(self):
        data = None
        if self.root:
            data = self.root.to_dict()
        with open(self.file, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self):
        try:
            with open(self.file, 'r') as f:
                data = json.load(f)
                self.root = Collaborator.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            # Si el archivo no existe o está vacío, empezamos con árbol vacío
            self.root = None

# ==================== Módulo 3: Gestión de Archivos con B-Tree ====================
class BTreeNode:
    def __init__(self, leaf: bool):
        self.leaf = leaf
        self.keys: List[str] = []
        self.values: List[str] = []
        self.children: List['BTreeNode'] = []

class BTree:
    def __init__(self, t: int):
        self.root = BTreeNode(True)
        self.t = t
        self.file = "btree.json"
        self.load()

    def insert(self, key: str, value: str):
        root = self.root
        if len(root.keys) == (2 * self.t) - 1:
            new_root = BTreeNode(False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert_non_full(self.root, key, value)
        self.save()

    def _insert_non_full(self, node: BTreeNode, key: str, value: str):
        # Implementación completa de inserción
        pass
    
    def search(self, key: str) -> Optional[str]:
        return self._search(self.root, key)

    def _search(self, node: BTreeNode, key: str) -> Optional[str]:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            return node.values[i]
        if node.leaf:
            return None
        return self._search(node.children[i], key)

    def save(self):
        data = self._serialize(self.root)
        with open(self.file, 'w') as f:
            json.dump(data, f)

    def load(self):
        try:
            with open(self.file, 'r') as f:
                data = json.load(f)
                self.root = self._deserialize(data)
        except FileNotFoundError:
            pass

    def _serialize(self, node: BTreeNode) -> dict:
        if not node:
            return None
        return {
            "leaf": node.leaf,
            "keys": node.keys,
            "values": node.values,
            "children": [self._serialize(child) for child in node.children]
        }

    def _deserialize(self, data: dict) -> BTreeNode:
        if not data:
            return None
        node = BTreeNode(data["leaf"])
        node.keys = data["keys"]
        node.values = data["values"]
        node.children = [self._deserialize(child) for child in data["children"]]
        return node

# ==================== Módulo 4: Gestión de Roles y Permisos (AVL) ====================
class AVLNode:
    def __init__(self, email: str, role: str, permissions: list):
        self.email = email
        self.role = role
        self.permissions = permissions
        self.left: Optional[AVLNode] = None
        self.right: Optional[AVLNode] = None
        self.height = 1

class RoleManager:
    def __init__(self):
        self.root = None
        self.file = "roles.json"
        self.load()
    def add_role(self, email: str, role: str, permissions: list):
            self.root = self._insert(self.root, email, role, permissions)
            self.save()

    def _insert(self, node: AVLNode, email: str, role: str, permissions: list) -> AVLNode:
        if not node:
            return AVLNode(email, role, permissions)
        
        if email < node.email:
            node.left = self._insert(node.left, email, role, permissions)
        else:
            node.right = self._insert(node.right, email, role, permissions)
        
        node.height = 1 + max(self._height(node.left), self._height(node.right))
        
        balance = self._get_balance(node)
        
        # Rotaciones
        if balance > 1:
            if email < node.left.email:
                return self._right_rotate(node)
            else:
                node.left = self._left_rotate(node.left)
                return self._right_rotate(node)
        if balance < -1:
            if email > node.right.email:
                return self._left_rotate(node)
            else:
                node.right = self._right_rotate(node.right)
                return self._left_rotate(node)
        return node

    def _height(self, node: AVLNode) -> int:
        return node.height if node else 0

    def _get_balance(self, node: AVLNode) -> int:
        return self._height(node.left) - self._height(node.right)

    def _left_rotate(self, z: AVLNode) -> AVLNode:
        y = z.right
        T2 = y.left
        
        y.left = z
        z.right = T2
        
        z.height = 1 + max(self._height(z.left), self._height(z.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        
        return y

    def _right_rotate(self, z: AVLNode) -> AVLNode:
        y = z.left
        T3 = y.right
        
        y.right = z
        z.left = T3
        
        z.height = 1 + max(self._height(z.left), self._height(z.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        
        return y

    # Resto de operaciones (update, remove, show, check, list)

    def save(self):
        data = self._serialize(self.root)
        with open(self.file, 'w') as f:
            json.dump(data, f)

    def load(self):
        try:
            with open(self.file, 'r') as f:
                data = json.load(f)
                self.root = self._deserialize(data)
        except FileNotFoundError:
            pass

    def _serialize(self, node: AVLNode) -> dict:
        if not node:
            return None
        return {
            "email": node.email,
            "role": node.role,
            "permissions": node.permissions,
            "left": self._serialize(node.left),
            "right": self._serialize(node.right),
            "height": node.height
        }

    def _deserialize(self, data: dict) -> AVLNode:
        if not data:
            return None
        node = AVLNode(data["email"], data["role"], data["permissions"])
        node.left = self._deserialize(data["left"])
        node.right = self._deserialize(data["right"])
        node.height = data["height"]
        return node
    
    def update_role(self, email: str, new_role: str, new_permissions: list):
        node = self._search(self.root, email)
        if node:
            node.role = new_role
            node.permissions = new_permissions
            self.save()

    def remove_role(self, email: str):
        self.root = self._delete_node(self.root, email)
        self.save()

    def _delete_node(self, root: Optional[AVLNode], email: str) -> Optional[AVLNode]:
        if not root:
            return root

        # Perform standard BST delete
        if email < root.email:
            root.left = self._delete_node(root.left, email)
        elif email > root.email:
            root.right = self._delete_node(root.right, email)
        else:
            # Node with only one child or no child
            if not root.left:
                return root.right
            elif not root.right:
                return root.left

            # Node with two children: Get the inorder successor (smallest in the right subtree)
            temp = self._min_value_node(root.right)
            root.email = temp.email
            root.role = temp.role
            root.permissions = temp.permissions
            root.right = self._delete_node(root.right, temp.email)

        # Update height of the current node
        root.height = 1 + max(self._height(root.left), self._height(root.right))

        # Get the balance factor
        balance = self._get_balance(root)

        # If the node is unbalanced, then balance it
        # Left Left Case
        if balance > 1 and self._get_balance(root.left) >= 0:
            return self._right_rotate(root)

        # Left Right Case
        if balance > 1 and self._get_balance(root.left) < 0:
            root.left = self._left_rotate(root.left)
            return self._right_rotate(root)

        # Right Right Case
        if balance < -1 and self._get_balance(root.right) <= 0:
            return self._left_rotate(root)

        # Right Left Case
        if balance < -1 and self._get_balance(root.right) > 0:
            root.right = self._right_rotate(root.right)
            return self._left_rotate(root)

        return root

    def _min_value_node(self, node: AVLNode) -> AVLNode:
        current = node
        while current.left is not None:
            current = current.left
        return current

    def show_role(self, email: str) -> Optional[Dict]:
        node = self._search(self.root, email)
        if node:
            return {"role": node.role, "permissions": node.permissions}
        return None

    def check_permission(self, email: str, action: str) -> bool:
        node = self._search(self.root, email)
        return node and action in node.permissions
    def _search(self, node: Optional[AVLNode], email: str) -> Optional[AVLNode]:
        """
        Busca un nodo en el árbol AVL basado en el correo electrónico.
        """
        if not node:
            return None
        if node.email == email:
            return node
        if email < node.email:
            return self._search(node.left, email)
        return self._search(node.right, email)
    
    def list_roles_postorder(self):
        roles = []
        self._postorder_traversal(self.root, roles)
        return roles

    def _postorder_traversal(self, node: AVLNode, result: list):
        if node:
            self._postorder_traversal(node.left, result)
            self._postorder_traversal(node.right, result)
            result.append(f"{node.email} ({node.role}): {', '.join(node.permissions)}")

# ==================== Sistema Principal y Comandos Completos ====================
class GitSystem:
    def __init__(self):
        self.branch_manager = BranchManager()
        self.collab_manager = CollaboratorBST()
        self.btree = BTree(3)
        self.role_manager = RoleManager()

    def handle_command(self, command: str):
        parts = command.split()
        if not parts or parts[0] != "git":
            print("Comando inválido")
            return

        try:
            cmd = parts[1]
            if cmd == "branch":
                self._handle_branch(parts[2:])
            elif cmd == "checkout":
                self._handle_checkout(parts[2:])
            elif cmd == "merge":
                self._handle_merge(parts[2:])
            elif cmd == "contributors":
                self._handle_contributors()
            elif cmd == "add-contributor":
                self._handle_add_contributor(parts[2:])
            elif cmd == "remove-contributor":
                self._handle_remove_contributor(parts[2:])
            elif cmd == "find-contributor":
                self._handle_find_contributor(parts[2:])
            elif cmd == "role":
                self._handle_role(parts[2:])
            else:
                print("Comando no reconocido")
        except IndexError as e:
            print(f"Error en parámetros: {str(e)}")

    def _handle_branch(self, args):
        if args[0] == "-d":
            self.branch_manager.delete_branch(args[1])
        elif args[0] == "--list":
            print("Ramas del repositorio:")
            self.branch_manager.list_branches_preorder()
        else:
            self.branch_manager.create_branch(args[0])

    def _handle_contributors(self):
        print("=== Colaboradores ===")
        self.collab_manager.list_preorder()

    def _handle_add_contributor(self, args):
        if len(args) != 2:
            print("Uso: git add-contributor <nombre> <rol>")
            return
        self.collab_manager.add(args[0], args[1])
        print(f" Colaborador {args[0]} agregado como {args[1]}")

    def _handle_remove_contributor(self, args):
        if len(args) != 1:
            print("Uso: git remove-contributor <nombre>")
            return
        self.collab_manager.remove(args[0])
        print(f" Colaborador {args[0]} eliminado")

    def _handle_find_contributor(self, args):
        if len(args) != 1:
            print("Uso: git find-contributor <nombre>")
            return
        collab = self.collab_manager.find(args[0])
        if collab:
            print(f" {collab.name} - Rol: {collab.role}")
        else:
            print(" Colaborador no encontrado")

    def _handle_role(self, args):
        if not args:
            print("Subcomando de rol requerido")
            return
        
        subcmd = args[0]
        if subcmd == "add":
            if len(args) != 4:
                print("Uso: git role add <email> <rol> <permisos,separados,por,comas>")
                return
            self.role_manager.add_role(args[1], args[2], args[3].split(','))
            print(f" Rol {args[2]} asignado a {args[1]}")
        
        elif subcmd == "update":
            if len(args) != 4:
                print("Uso: git role update <email> <nuevo_rol> <nuevos_permisos>")
                return
            self.role_manager.update_role(args[1], args[2], args[3].split(','))
            print(f" Rol actualizado para {args[1]}")
        
        elif subcmd == "remove":
            if len(args) != 2:
                print("Uso: git role remove <email>")
                return
            self.role_manager.remove_role(args[1])
            print(f" Rol eliminado para {args[1]}")
        
        elif subcmd == "show":
            if len(args) != 2:
                print("Uso: git role show <email>")
                return
            info = self.role_manager.show_role(args[1])
            if info:
                print(f" {args[1]}: Rol={info['role']}, Permisos={', '.join(info['permissions'])}")
            else:
                print(" Usuario no encontrado")
        
        elif subcmd == "check":
            if len(args) != 3:
                print("Uso: git role check <email> <acción>")
                return
            has_permission = self.role_manager.check_permission(args[1], args[2])
            print(f" Permiso {'OTORGADO' if has_permission else ' DENEGADO'} para {args[2]}")
        
        elif subcmd == "list":
            print("=== Lista de Roles ===")
            for entry in self.role_manager.list_roles_postorder():
                print(f"• {entry}")
        
        else:
            print("Subcomando de rol no reconocido")
    def _handle_checkout(self, args):
        if len(args) != 1:
            print("Uso: git checkout <rama>")
            return
        branch_name = args[0]
        if self.branch_manager.checkout(branch_name):
            print(f" Cambiado a la rama {branch_name}")
        else:
            print(f" Rama {branch_name} no encontrada")

# ==================== Ejecución Principal ====================
if __name__ == "__main__":
    system = GitSystem()
    print(" Sistema Git mejorado - Equipo 3")
    print("Comandos soportados:")
    print("- git branch [--list | -d | <nombre>]")
    print("- git checkout <rama>")
    print("- git merge <origen> <destino>")
    print("- git contributors")
    print("- git add-contributor <nombre> <rol>")
    print("- git remove-contributor <nombre>")
    print("- git find-contributor <nombre>")
    print("- git role [add|update|remove|show|check|list] ...")
    
    while True:
        try:
            command = input("\n git> ")
            if command.lower() == "exit":
                break
            system.handle_command(command)
        except KeyboardInterrupt:
            print("\n Saliendo del sistema...")
            break