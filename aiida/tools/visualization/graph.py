# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" provides functionality to create graphs of the AiiDa data providence,
*via* graphviz.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import six
from graphviz import Digraph
from aiida.orm import load_node, Data, ProcessNode
from aiida.orm.querybuilder import QueryBuilder
from aiida.common import LinkType
from aiida.orm.utils.links import LinkPair

__all__ = ('Graph', 'default_link_styles', 'default_node_styles', 'pstate_node_styles', 'default_node_sublabels')


def default_link_styles(link_pair, add_label, add_type):
    # type: (LinkPair, bool, bool) -> dict
    """map link_pair to a graphviz edge style

    :param link_type: a LinkPair attribute
    :type link_type: aiida.orm.utils.links.LinkPair
    :param add_label: include link label
    :type add_label: bool
    :param add_type: include link type
    :type add_type: bool
    :rtype: dict

    """
    style = {
        LinkType.INPUT_CALC: {
            "style": "solid",
            "color": "#000000"  # black
        },
        LinkType.INPUT_WORK: {
            "style": "dashed",
            "color": "#000000"  # black
        },
        LinkType.CALL_CALC: {
            "style": "dotted",
            "color": "#000000"  # black
        },
        LinkType.CALL_WORK: {
            "style": "dotted",
            "color": "#000000"  # black
        },
        LinkType.CREATE: {
            "style": "solid",
            "color": "#000000"  # black
        },
        LinkType.RETURN: {
            "style": "dashed",
            "color": "#000000"  # black
        }
    }[link_pair.link_type]

    if add_label and not add_type:
        style['label'] = link_pair.link_label
    elif add_type and not add_label:
        style['label'] = link_pair.link_type.name
    elif add_label and add_type:
        style['label'] = "{}\n{}".format(link_pair.link_type.name, link_pair.link_label)

    return style


def default_node_styles(node):
    """map a node to a graphviz node style

    :param node: the node to map
    :type node: aiida.orm.nodes.node.Node
    :rtype: dict

    """
    class_node_type = node.class_node_type

    try:
        default = node.get_style_default()
    except AttributeError:
        default = {
            "shape": "ellipse",
            "style": "filled",
            "fillcolor": "#8cd499ff",  # green,
            "penwidth": 0
        }

    node_type_map = {
        "data.code.Code.": {
            "shape": "ellipse",
            "style": "filled",
            "fillcolor": "#4ca4b9aa",  # blue
            "penwidth": 0
        },
        "process.calculation.calcjob.CalcJobNode.": {
            "shape": "rectangle",
            "style": "filled",
            "fillcolor": "#de707fff",  # red
            "penwidth": 0
        },
        "process.calculation.calcfunction.CalcFunctionNode.": {
            "shape": "rectangle",
            "style": "filled",
            "fillcolor": "#de707f77",  # red
            "penwidth": 0
        },
        "process.workflow.workchain.WorkChainNode.": {
            "shape": "rectangle",
            "style": "filled",
            "fillcolor": "#e38851ff",  # orange
            "penwidth": 0
        },
        "process.workflow.workfunction.WorkFunctionNode.": {
            "shape": "rectangle",
            "style": "filled",
            "fillcolor": "#e38851ff",  # orange
            "penwidth": 0
        }
    }

    node_style = node_type_map.get(class_node_type, default)

    return node_style


def pstate_node_styles(node):
    """map a process node to a graphviz node style

    :param node: the node to map
    :type node: aiida.orm.nodes.node.Node
    :rtype: dict

    """
    class_node_type = node.class_node_type

    default = {"shape": "rectangle", "pencolor": "black"}

    process_map = {
        "process.calculation.calcjob.CalcJobNode.": {
            "shape": "ellipse",
            "style": "filled",
            "penwidth": 0,
            "fillcolor": "#ffffffff"
        },
        "process.calculation.calcfunction.CalcFunctionNode.": {
            "shape": "ellipse",
            "style": "filled",
            "penwidth": 0,
            "fillcolor": "#ffffffff"
        },
        "process.workflow.workchain.WorkChainNode.": {
            "shape": "polygon",
            "sides": "6",
            "style": "filled",
            "penwidth": 0,
            "fillcolor": "#ffffffff"
        },
        "process.workflow.workfunction.WorkFunctionNode.": {
            "shape": "polygon",
            "sides": "6",
            "style": "filled",
            "penwidth": 0,
            "fillcolor": "#ffffffff"
        }
    }

    node_style = process_map.get(class_node_type, default)

    if isinstance(node, ProcessNode):
        # style process node, based on success/failure of process
        if node.is_failed or node.is_excepted or node.is_killed:
            node_style['fillcolor'] = '#de707fff'  # red
        elif node.is_finished_ok:
            node_style['fillcolor'] = '#8cd499ff'  # green
        else:
            # Note: this conditional will hit the states CREATED, WAITING and RUNNING
            node_style['fillcolor'] = '#e38851ff'  # orange

    return node_style


def default_node_sublabels(node):
    """function mapping nodes to a sublabel
    (e.g. specifying some attribute values)

    :param node: the node to map
    :type node: aiida.orm.nodes.node.Node
    :rtype: str

    """
    # pylint: disable=too-many-branches

    class_node_type = node.class_node_type
    if class_node_type == "data.int.Int.":
        sublabel = "value: {}".format(node.get_attribute("value", ""))
    elif class_node_type == "data.float.Float.":
        sublabel = "value: {}".format(node.get_attribute("value", ""))
    elif class_node_type == "data.str.Str.":
        sublabel = "{}".format(node.get_attribute("value", ""))
    elif class_node_type == "data.bool.Bool.":
        sublabel = "{}".format(node.get_attribute("value", ""))
    elif class_node_type == "data.code.Code.":
        sublabel = "{}@{}".format(os.path.basename(node.get_execname()), node.get_computer_name())
    elif class_node_type == "data.singlefile.SinglefileData.":
        sublabel = node.filename
    elif class_node_type == "data.remote.RemoteData.":
        sublabel = "@{}".format(node.get_computer_name())
    elif class_node_type == "data.structure.StructureData.":
        sublabel = node.get_formula()
    elif class_node_type == "data.cif.CifData.":
        formulae = [str(f).replace(" ", "") for f in node.get_formulae() or []]
        sg_numbers = [str(s) for s in node.get_spacegroup_numbers() or []]
        sublabel_lines = []
        if formulae:
            sublabel_lines.append(", ".join(formulae))
        if sg_numbers:
            sublabel_lines.append(", ".join(sg_numbers))
        sublabel = "; ".join(sublabel_lines)
    elif class_node_type == "data.upf.UpfData.":
        sublabel = "{}".format(node.get_attribute("element", ""))
    elif isinstance(node, ProcessNode):
        sublabel = []
        if node.process_state is not None:
            sublabel.append("State: {}".format(node.process_state.value))
        if node.exit_status is not None:
            sublabel.append("Exit Code: {}".format(node.exit_status))
        sublabel = "\n".join(sublabel)
    else:
        sublabel = node.get_description()

    return sublabel


def get_node_id_label(node, id_type):
    """return an identifier str for the node """
    if id_type == "pk":
        return node.pk
    if id_type == "uuid":
        return node.uuid.split("-")[0]
    if id_type == "label":
        return node.label
    raise ValueError("node_id_type not recognised: {}".format(id_type))


def _add_graphviz_node(graph,
                       node,
                       node_style_func,
                       node_sublabel_func,
                       style_override=None,
                       include_sublabels=True,
                       id_type="pk"):
    """create a node in the graph

    The first line of the node text is always '<node.name> (<node.pk>)'.
    Then, if ``include_sublabels=True``, subsequent lines are added,
    which are node type dependant.

    :param graph: the graphviz.Digraph to add the node to
    :param node: the node to add
    :type node: aiida.orm.nodes.node.Node
    :param node_style_func: callable mapping a node instance to a dictionary defining the graphviz node style
    :param node_sublabel_func: callable mapping a node instance to a sub-label for the node text
    :param style_override: style dictionary, whose keys will override the final computed style
    :type style_override: None or dict
    :param include_sublabels: whether to include the sublabels for nodes
    :type include_sublabels: bool
    :param id_type: the type of identifier to use for node labels ('pk' or 'uuid')
    :type id_type: str

    nodes are styled based on the node type

    For subclasses of Data, the ``class_node_type`` attribute is used
    for mapping to type specific styles

    For subclasses of ProcessNode, we choose styles to distinguish between
    types, and also color the nodes for successful/failed processes

    """
    # pylint: disable=too-many-arguments
    node_style = {}
    if isinstance(node, Data):

        node_style = node_style_func(node)
        label = ["{} ({})".format(node.__class__.__name__, get_node_id_label(node, id_type))]

    elif isinstance(node, ProcessNode):

        node_style = node_style_func(node)

        label = [
            "{} ({})".format(node.__class__.__name__ if node.process_label is None else node.process_label,
                             get_node_id_label(node, id_type))
        ]

    if include_sublabels:
        sublabel = node_sublabel_func(node)
        if sublabel:
            label.append(sublabel)

    node_style["label"] = "\n".join(label)

    if style_override is not None:
        node_style.update(style_override)

    # coerce node style values to strings, required by graphviz
    node_style = {k: str(v) for k, v in node_style.items()}

    return graph.node("N{}".format(node.pk), **node_style)


def _add_graphviz_edge(graph, in_node, out_node, style=None):
    """add graphviz edge between two nodes

    :param graph: the graphviz.DiGraph to add the edge to
    :param in_node: the head node
    :param out_node: the tail node
    :param style: the graphviz style (Default value = None)
    :type style: dict or None

    """
    if style is None:
        style = {}

    # coerce node style values to strings
    style = {k: str(v) for k, v in style.items()}

    return graph.edge("N{}".format(in_node.pk), "N{}".format(out_node.pk), **style)


class Graph(object):
    """a class to create graphviz graphs of the AiiDA node provenance"""

    # pylint: disable=useless-object-inheritance

    def __init__(self,
                 engine=None,
                 graph_attr=None,
                 global_node_style=None,
                 global_edge_style=None,
                 include_sublabels=True,
                 link_style_fn=None,
                 node_style_fn=None,
                 node_sublabel_fn=None,
                 node_id_type="pk"):
        """a class to create graphviz graphs of the AiiDA node provenance

        Nodes and edges, are cached, so that they are only created once

        :param engine: the graphviz engine, e.g. dot, circo (Default value = None)
        :type engine: str or None
        :param graph_attr: attributes for the graphviz graph (Default value = None)
        :type graph_attr: dict or None
        :param global_node_style: styles which will be added to all nodes.
            Note this will override any builtin attributes (Default value = None)
        :type global_node_style: dict or None
        :param global_edge_style: styles which will be added to all edges.
            Note this will override any builtin attributes (Default value = None)
        :type global_edge_style: dict or None
        :param include_sublabels: if True, the note text will include node dependant sub-labels (Default value = True)
        :type include_sublabels: bool
        :param link_style_fn: callable mapping LinkType to graphviz style dict;
            link_style_fn(link_type) -> dict (Default value = None)
        :param node_sublabel_fn: callable mapping nodes to a graphviz style dict;
            node_sublabel_fn(node) -> dict (Default value = None)
        :param node_sublabel_fn: callable mapping data node to a sublabel (e.g. specifying some attribute values)
            node_sublabel_fn(node) -> str (Default value = None)
        :param node_id_type: the type of identifier to within the node text ('pk', 'uuid' or 'label')
        :type node_id_type: str

        """
        # pylint: disable=too-many-arguments
        self._graph = Digraph(engine=engine, graph_attr=graph_attr)
        self._nodes = set()
        self._edges = set()
        self._global_node_style = global_node_style or {}
        self._global_edge_style = global_edge_style or {}
        self._include_sublabels = include_sublabels
        self._link_styles = link_style_fn or default_link_styles
        self._node_styles = node_style_fn or default_node_styles
        self._node_sublabels = node_sublabel_fn or default_node_sublabels
        self._node_id_type = node_id_type

    @property
    def graphviz(self):
        """return a copy of the graphviz.Digraph"""
        return self._graph.copy()

    @property
    def nodes(self):
        """return a copy of the nodes"""
        return self._nodes.copy()

    @property
    def edges(self):
        """return a copy of the edges"""
        return self._edges.copy()

    @staticmethod
    def _load_node(node):
        """ load a node (if not already loaded)

        :param node: node or node pk/uuid
        :type node: int or str or aiida.orm.nodes.node.Node
        :returns: aiida.orm.nodes.node.Node

        """
        if isinstance(node, (int, six.string_types)):
            return load_node(node)
        return node

    def add_node(self, node, style_override=None, overwrite=False):
        """add single node to the graph

        :param node: node or node pk/uuid
        :type node: int or str or aiida.orm.nodes.node.Node
        :param style_override: graphviz style parameters that will override default values
        :type style_override: dict or None
        :param overwrite: whether to overrite an existing node (Default value = False)
        :type overwrite: bool

        """
        node = self._load_node(node)
        style = {} if style_override is None else style_override
        style.update(self._global_node_style)
        if node.pk not in self._nodes or overwrite:
            _add_graphviz_node(
                self._graph,
                node,
                node_style_func=self._node_styles,
                node_sublabel_func=self._node_sublabels,
                style_override=style,
                include_sublabels=self._include_sublabels,
                id_type=self._node_id_type)
            self._nodes.add(node.pk)

    def add_edge(self, in_node, out_node, link_pair=None, style=None, overwrite=False):
        """add single node to the graph

        :param in_node: node or node pk/uuid
        :type in_node: int or aiida.orm.nodes.node.Node
        :param out_node: node or node pk/uuid
        :type out_node: int or str or aiida.orm.nodes.node.Node
        :param link_pair: defining the relationship between the nodes
        :type link_pair: None or aiida.orm.utils.links.LinkPair
        :param style: graphviz style parameters (Default value = None)
        :type style: dict or None
        :param overwrite: whether to overrite existing edge (Default value = False)
        :type overwrite: bool

        """
        in_node = self._load_node(in_node)
        if in_node.pk not in self._nodes:
            raise AssertionError("in_node pk={} must have already been added to the graph".format(in_node.pk))
        out_node = self._load_node(out_node)
        if out_node.pk not in self._nodes:
            raise AssertionError("out_node pk={} must have already been added to the graph".format(out_node.pk))

        if (in_node.pk, out_node.pk, link_pair) in self._edges and not overwrite:
            return

        style = {} if style is None else style
        self._edges.add((in_node.pk, out_node.pk, link_pair))
        style.update(self._global_edge_style)

        _add_graphviz_edge(self._graph, in_node, out_node, style)

    @staticmethod
    def _convert_link_types(link_types):
        """ convert link types, which may be strings, to a member of LinkType
        """
        if link_types is None:
            return None
        if isinstance(link_types, six.string_types):
            link_types = [link_types]
        link_types = tuple([getattr(LinkType, l.upper()) if isinstance(l, six.string_types) else l for l in link_types])
        return link_types

    def add_incoming(self, node, link_types=(), annotate_links=None, return_pks=True):
        """add nodes and edges for incoming links to a node

        :param node: node or node pk/uuid
        :type node: aiida.orm.nodes.node.Node or int
        :param link_types: filter by link types (Default value = ())
        :type link_types: str or tuple[str] or aiida.common.links.LinkType or tuple[aiida.common.links.LinkType]
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = None)
        :type annotate_links: bool or str
        :param return_pks: whether to return a list of nodes, or list of node pks (Default value = True)
        :type return_pks: bool
        :returns: list of nodes or node pks

        """
        if annotate_links not in [None, False, "label", "type", "both"]:
            raise AssertionError('annotate_links must be one of False, "label", "type" or "both"')

        self.add_node(node)

        nodes = []
        for link_triple in node.get_incoming(link_type=self._convert_link_types(link_types)).link_triples:
            self.add_node(link_triple.node)
            link_pair = LinkPair(link_triple.link_type, link_triple.link_label)
            style = self._link_styles(
                link_pair, add_label=annotate_links in ["label", "both"], add_type=annotate_links in ["type", "both"])
            self.add_edge(link_triple.node, node, link_pair, style=style)
            nodes.append(link_triple.node.pk if return_pks else link_triple.node)

        return nodes

    def add_outgoing(self, node, link_types=(), annotate_links=None, return_pks=True):
        """add nodes and edges for outgoing links to a node

        :param node: node or node pk
        :type node: aiida.orm.nodes.node.Node or int
        :param link_types: filter by link types (Default value = ())
        :type link_types: str or tuple[str] or aiida.common.links.LinkType or tuple[aiida.common.links.LinkType]
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = None)
        :type annotate_links: bool or str
        :param return_pks: whether to return a list of nodes, or list of node pks (Default value = True)
        :type return_pks: bool
        :returns: list of nodes or node pks

        """
        if annotate_links not in [None, False, "label", "type", "both"]:
            raise AssertionError('annotate_links must be one of False, "label", "type" or "both"')

        self.add_node(node)

        nodes = []
        for link_triple in node.get_outgoing(link_type=self._convert_link_types(link_types)).link_triples:
            self.add_node(link_triple.node)
            link_pair = LinkPair(link_triple.link_type, link_triple.link_label)
            style = self._link_styles(
                link_pair, add_label=annotate_links in ["label", "both"], add_type=annotate_links in ["type", "both"])
            self.add_edge(node, link_triple.node, link_pair, style=style)
            nodes.append(link_triple.node.pk if return_pks else link_triple.node)

        return nodes

    def recurse_descendants(self,
                            origin,
                            depth=None,
                            link_types=(),
                            annotate_links=False,
                            origin_style=(),
                            include_process_inputs=False,
                            print_func=None):
        """add nodes and edges from an origin recursively,
        following outgoing links

        :param origin: node or node pk/uuid
        :type origin: aiida.orm.nodes.node.Node or int
        :param depth: if not None, stop after travelling a certain depth into the graph (Default value = None)
        :type depth: None or int
        :param link_types: filter by subset of link types (Default value = ())
        :type link_types: tuple or str
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool or str
        :param origin_style: node style map for origin node (Default value = ())
        :type origin_style: dict or tuple
        :param include_calculation_inputs: include incoming links for all processes (Default value = False)
        :type include_calculation_inputs: bool
        :param print_func: a function to stream information to, i.e. print_func(str)

        """
        # pylint: disable=too-many-arguments
        origin_node = self._load_node(origin)

        self.add_node(origin_node, style_override=dict(origin_style))

        leaf_nodes = [origin_node]
        traversed_pks = [origin_node.pk]
        cur_depth = 0
        while leaf_nodes:
            cur_depth += 1
            # checking of maximum descendant depth is set and applies.
            if depth is not None and cur_depth > depth:
                break
            if print_func:
                print_func("- Depth: {}".format(cur_depth))
            new_nodes = []
            for node in leaf_nodes:
                outgoing_nodes = self.add_outgoing(
                    node, link_types=link_types, annotate_links=annotate_links, return_pks=False)
                if outgoing_nodes and print_func:
                    print_func("  {} -> {}".format(node.pk, [on.pk for on in outgoing_nodes]))
                new_nodes.extend(outgoing_nodes)

                if include_process_inputs and isinstance(node, ProcessNode):
                    self.add_incoming(node, link_types=link_types, annotate_links=annotate_links)

            # ensure the same path isn't traversed multiple times
            leaf_nodes = []
            for new_node in new_nodes:
                if new_node.pk in traversed_pks:
                    continue
                leaf_nodes.append(new_node)
                traversed_pks.append(new_node.pk)

    def recurse_ancestors(self,
                          origin,
                          depth=None,
                          link_types=(),
                          annotate_links=False,
                          origin_style=(),
                          include_process_outputs=False,
                          print_func=None):
        """add nodes and edges from an origin recursively,
        following incoming links

        :param origin: node or node pk/uuid
        :type origin: aiida.orm.nodes.node.Node or int
        :param depth: if not None, stop after travelling a certain depth into the graph (Default value = None)
        :type depth: None or int
        :param link_types: filter by subset of link types (Default value = ())
        :type link_types: tuple or str
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool
        :param origin_style: node style map for origin node (Default value = ())
        :type origin_style: dict or tuple
        :param include_process_outputs:  include outgoing links for all processes (Default value = False)
        :type include_process_outputs: bool
        :param print_func: a function to stream information to, i.e. print_func(str)

        """
        # pylint: disable=too-many-arguments
        origin_node = self._load_node(origin)

        self.add_node(origin_node, style_override=dict(origin_style))

        last_nodes = [origin_node]
        traversed_pks = [origin_node.pk]
        cur_depth = 0
        while last_nodes:
            cur_depth += 1
            # checking of maximum descendant depth is set and applies.
            if depth is not None and cur_depth > depth:
                break
            if print_func:
                print_func("- Depth: {}".format(cur_depth))
            new_nodes = []
            for node in last_nodes:
                incoming_nodes = self.add_incoming(
                    node, link_types=link_types, annotate_links=annotate_links, return_pks=False)
                if incoming_nodes and print_func:
                    print_func("  {} -> {}".format(node.pk, [n.pk for n in incoming_nodes]))
                new_nodes.extend(incoming_nodes)

                if include_process_outputs and isinstance(node, ProcessNode):
                    self.add_outgoing(node, link_types=link_types, annotate_links=annotate_links)

            # ensure the same path isn't traversed multiple times
            last_nodes = []
            for new_node in new_nodes:
                if new_node.pk in traversed_pks:
                    continue
                last_nodes.append(new_node)
                traversed_pks.append(new_node.pk)

    def add_origin_to_targets(self,
                              origin,
                              target_cls,
                              target_filters=None,
                              include_target_inputs=False,
                              include_target_outputs=False,
                              origin_style=(),
                              annotate_links=False):
        """Add nodes and edges from an origin node to all nodes of a target node class.

        :param origin: node or node pk/uuid
        :type origin: aiida.orm.nodes.node.Node or int
        :param target_cls: target node class
        :param target_filters:  (Default value = None)
        :type target_filters: dict or None
        :param include_target_inputs:  (Default value = False)
        :type include_target_inputs: bool
        :param include_target_outputs:  (Default value = False)
        :type include_target_outputs: bool
        :param origin_style: node style map for origin node (Default value = ())
        :type origin_style: dict or tuple
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool

        """
        # pylint: disable=too-many-arguments
        origin_node = self._load_node(origin)

        if target_filters is None:
            target_filters = {}

        self.add_node(origin_node, style_override=dict(origin_style))

        query = QueryBuilder(
            **{
                "path": [{
                    'cls': origin_node.__class__,
                    "filters": {
                        "id": origin_node.pk
                    },
                    'tag': "origin"
                },
                         {
                             'cls': target_cls,
                             'filters': target_filters,
                             'with_ancestors': 'origin',
                             'tag': "target",
                             'project': "*"
                         }]
            })

        for (target_node,) in query.iterall():
            self.add_node(target_node)
            self.add_edge(origin_node, target_node, style={'style': 'dashed', 'color': 'grey'})

            if include_target_inputs:
                self.add_incoming(target_node, annotate_links=annotate_links)

            if include_target_outputs:
                self.add_outgoing(target_node, annotate_links=annotate_links)

    def add_origins_to_targets(self,
                               origin_cls,
                               target_cls,
                               origin_filters=None,
                               target_filters=None,
                               include_target_inputs=False,
                               include_target_outputs=False,
                               origin_style=(),
                               annotate_links=False):
        """Add nodes and edges from all nodes of an origin class to all node of a target node class.

        :param origin_cls: origin node class
        :param target_cls: target node class
        :param origin_filters:  (Default value = None)
        :type origin_filters: dict or None
        :param target_filters:  (Default value = None)
        :type target_filters: dict or None
        :param include_target_inputs:  (Default value = False)
        :type include_target_inputs: bool
        :param include_target_outputs:  (Default value = False)
        :type include_target_outputs: bool
        :param origin_style: node style map for origin node (Default value = ())
        :type origin_style: dict or tuple
        :param annotate_links: label edges with the link 'label', 'type' or 'both' (Default value = False)
        :type annotate_links: bool

        """
        # pylint: disable=too-many-arguments
        if origin_filters is None:
            origin_filters = {}

        query = QueryBuilder(
            **{"path": [{
                'cls': origin_cls,
                "filters": origin_filters,
                'tag': "origin",
                'project': "*"
            }]})

        for (node,) in query.iterall():
            self.add_origin_to_targets(
                node,
                target_cls,
                target_filters=target_filters,
                include_target_inputs=include_target_inputs,
                include_target_outputs=include_target_outputs,
                origin_style=origin_style,
                annotate_links=annotate_links)
