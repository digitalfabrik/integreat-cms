import logging

from django.core.management.base import CommandError

from ....cms.models import Page
from ..log_command import LogCommand

logger = logging.getLogger(__name__)


class Command(LogCommand):
    """
    Management command to repair a broken Treebeard page tree
    """

    help = "Repair broken tree structure"
    pages_seen = None

    def add_arguments(self, parser):
        """
        Define the arguments of this command

        :param parser: The argument parser
        :type parser: ~django.core.management.base.CommandParser
        """
        parser.add_argument(
            "page_id", type=int, help="The ID of a page belonging to the broken tree."
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Whether changes should be written to the database",
        )

    # pylint: disable=arguments-differ
    def handle(self, *args, page_id, commit, **options):
        r"""
        Try to run the command

        :param \*args: The supplied arguments
        :type \*args: list

        :param page_id: The page ID (node) of a broken tree
        :type page_id: int

        :param commit: Whether changes should be written to the database
        :type commit: bool

        :param \**options: The supplied keyword options
        :type \**options: dict

        :raises ~django.core.management.base.CommandError: When the input is invalid
        """
        try:
            root_node = Page.objects.get(id=page_id)
        except Page.DoesNotExist as e:
            raise CommandError(f'The page with id "{page_id}" does not exist.') from e
        # Traversing to root node
        while root_node.parent:
            root_node = root_node.parent
        action = "Fixing" if commit else "Detecting problems in"
        self.print_info(f"{action} tree with id {root_node.tree_id}...")
        self.pages_seen = []
        self.calculate_left_right_values(root_node, 1, commit)
        self.check_for_orphans(root_node.tree_id)

    def check_tree_fields(self, tree_node, left, right):
        """
        Check whether the tree fields are correct

        :param tree_node: The current node
        :type tree_node: ~integreat_cms.cms.models.pages.page.Page

        :param left: The new left value of the node
        :type left: int

        :param right: The new right value of the node
        :type right: int

        :return: Whether the tree fields of the node are valid
        :rtype: bool
        """
        valid = True
        self.stdout.write(self.bold(f"Page {tree_node.id}:"))
        self.print_success(f"\tparent_id: {tree_node.parent_id}")
        if not tree_node.parent or tree_node.tree_id == tree_node.parent.tree_id:
            self.print_success(f"\ttree_id: {tree_node.tree_id}")
        else:
            self.print_error(
                f"\ttree_id: {tree_node.tree_id} → {tree_node.parent.tree_id}"
            )
            valid = False
        if tree_node.parent_id:
            if tree_node.depth == tree_node.parent.depth + 1:
                self.print_success(f"\tdepth: {tree_node.depth}")
            else:
                self.print_error(
                    f"\tdepth: {tree_node.depth} → {tree_node.parent.depth + 1}"
                )
                valid = False
        elif tree_node.depth == 1:
            self.print_success(f"\tdepth: {tree_node.depth}")
        else:
            self.print_error(f"\tdepth: {tree_node.depth} → 1")
            valid = False
        if tree_node.lft == left:
            self.print_success(f"\tlft: {tree_node.lft}")
        else:
            self.print_error(f"\tlft: {tree_node.lft} → {left}")
            valid = False
        if tree_node.rgt == right:
            self.print_success(f"\trgt: {tree_node.rgt}")
        else:
            self.print_error(f"\trgt: {tree_node.rgt} → {right}")
            valid = False
        return valid

    def check_for_orphans(self, tree_id):
        """
        Check whether orphans exist (pages with the same tree_id, but its ancestors are in another tree)

        :param tree_id: The current tree id
        :type tree_id: int
        """
        if orphans := Page.objects.filter(tree_id=tree_id).exclude(
            id__in=self.pages_seen
        ):
            self.print_error(
                "\n💣 Orphans detected! The following pages share the tree id "
                f"{tree_id} but don't have a relation to the root node:"
            )
            for orphan in orphans:
                self.stdout.write(self.bold(f"Page {orphan.id}:"))
                self.print_error(
                    f"\tparent_id: {orphan.parent_id}\n"
                    f"\tparent.tree_id: {orphan.parent.tree_id}"
                )
                self.stdout.write(
                    self.bold(
                        f"\tdepth {orphan.depth}\n"
                        f"\tlft: {orphan.lft}\n"
                        f"\trgt: {orphan.rgt}"
                    )
                )

    def calculate_left_right_values(self, tree_node, left, commit):
        """
        Recursively calculate the left and right value for a given node and its
        children.

        :param tree_node: A node of a MPTT tree
        :type tree_node: ~integreat_cms.cms.models.pages.page.Page

        :param left: The new left value of the node
        :type left: int

        :param commit: Whether changes should be written to the database
        :type commit: bool

        :return: The new right value of the node
        :rtype: int
        """
        right = left

        for child in tree_node.children.all():
            right = self.calculate_left_right_values(child, right + 1, commit)

        right += 1

        valid = self.check_tree_fields(tree_node, left, right)

        if not valid and commit:
            if tree_node.parent:
                tree_node.tree_id = tree_node.parent.tree_id
                tree_node.depth = tree_node.parent.depth + 1
            tree_node.rgt = right
            tree_node.lft = left
            tree_node.save()
            logger.info("Fixed tree fields of %r", tree_node)

        self.pages_seen.append(tree_node.id)

        return right
