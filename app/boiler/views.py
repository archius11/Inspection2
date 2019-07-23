from flask import render_template, session, redirect, url_for, current_app, flash, abort, json, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.sql.expression import func
from . import boiler
from .forms import CreateBoilerForm, CreateBoilerNodesForm, NodeSelectForm
from .. import db
from ..models import Company, Boiler, Permission, Node, Norm, Measurement


from ..decorators import permission_required

# =====================================================
# BOILER ROUTES
# =====================================================


@boiler.route('/create', methods=["GET", "POST"])  # create boiler
@login_required
@permission_required(Permission.CREATE_BOILER)
def create_boiler():
    form = CreateBoilerForm()
    if form.validate_on_submit():
        new_boiler = Boiler(boiler_name=form.boiler_name.data,
                        company_id=int(form.company.data))
        db.session.add(new_boiler)
        db.session.commit()
        flash("New boiler created")
        return redirect(url_for("boiler.add_nodes", id=new_boiler.id))
    return render_template("boiler/create_boiler.html", form=form)


@boiler.route('<int:id>/add-nodes', methods=["GET", "POST"])  # add boiler structure and norms
@login_required
@permission_required(Permission.CREATE_BOILER)
def add_nodes(id):
    boiler_id = id
    with open('app/static/default_nodes.json', 'r') as f:
        default_structure = json.load(f)

    form = CreateBoilerNodesForm()

    if request.method == 'POST':
        updated_structure = request.get_json()['structure']
        print("updated_structure: " + str(len(updated_structure)))
        print("before add_nodes_to_db")
        add_nodes_to_db(updated_structure, boiler_id)
        print("after add_nodes_to_db")
        print("nodes created")
        flash("Nodes created")
        # return render_template("boiler/show_boiler.html", id=boiler_id)

    return render_template('boiler/add_nodes.html', id=id, form=form, structure=default_structure)


@boiler.route('/<int:id>')  # show boiler info
@login_required
def show_boiler(id):
    boiler = Boiler.query.filter_by(id=id).first_or_404()
    if not current_user.company_access(boiler.company_id):
        abort(403)
    company = Company.query.filter_by(id=boiler.company_id).first()
    form = NodeSelectForm(boiler_id=boiler.id)
    return render_template('boiler/show_boiler.html', boiler=boiler, company=company, form=form)


@boiler.route('/edit-boiler/<id>', methods=["GET", "POST"])  # edit boiler info
@login_required
@permission_required(Permission.CREATE_BOILER)
def edit_boiler(id):
    boiler = Boiler.query.get_or_404(id)
    form = CreateBoilerForm(boiler=boiler)
    if form.validate_on_submit():
        boiler.boiler_name = form.boiler_name.data
        boiler.company = Company.query.get(form.company.data)
        db.session.add(boiler)
        db.session.commit()
        flash("The boiler has been updated.")
        return redirect(url_for('boiler.show_boiler', id=id))
    form.boiler_name.data = boiler.boiler_name
    form.company.data = boiler.company
    return render_template('boiler/edit_boiler.html', boiler=boiler, form=form)


# =============================
# AUXILIARY ROUTES
# =============================


@boiler.route('/default_structure', methods=["GET"])
@login_required
def structure():
    with open('app/static/default_nodes.json', 'r') as f:
        structure = json.load(f)
    return jsonify(structure)


@boiler.route('/children/<node>', methods=["GET", "POST"])  # get json with children nodes
@login_required
def level(node):
    level_elements = Node.query.filter_by(parent_id=node).all()
    level_array = [element.as_dict() for element in level_elements]
    return jsonify(level_array)


@boiler.route('/table/<node>', methods=["GET", "POST"])  # get json with measurements of chosen node
@login_required
def table(node):

    ''' SELECT nodes.id, nodes.node_name, measurements.measure_date, COALESCE(measurements.value, 0),
    norms."default", norms.minor, norms.major, norms.defect
    FROM public.nodes as nodes
    LEFT JOIN public.norms as norms
    ON nodes.id = norms.node_id
    LEFT JOIN public.measurements as measurements
    ON nodes.id = measurements.node_id
    WHERE parent_id = 3
    ORDER BY nodes.id; '''

    table_query = db.session.query(Node.node_name, Measurement.measure_date, Measurement.value, Norm.default, Norm.minor,
                         Norm.major, Norm.defect). \
        outerjoin(Norm, Norm.node_id == Node.id). \
        outerjoin(Measurement, Measurement.node_id == Node.id). \
        filter(Node.parent_id == node). \
        filter(Measurement.value != None).all()

    table_dic = {}

    for node in table_query:
        year = node[1].year
        if not str(year) in table_dic:
            table_dic[str(year)] = []
        table_dic[str(year)].append(node)

    return jsonify(table_dic)


def add_nodes_to_db(structure, boiler_id):

    last_id = db.session.query(func.max(Node.id)).first()[0]

    if last_id == None:
        current_id = 1
    else:
        current_id = last_id + 1

    for block in structure:
        new_block = Node(boiler_id=boiler_id,
                         index=block.get('index'),
                         node_name=block.get('node_name'),
                         id = current_id
                         )
        db.session.add(new_block)
        current_id += 1

        for child_1 in block.get('children'):
            new_child_1 = Node(boiler_id=boiler_id,
                               parent_id=new_block.id,
                               index=child_1.get('index'),
                               node_name=child_1.get('node_name'),
                               id = current_id
                               )
            db.session.add(new_child_1)
            current_id += 1

            for child_2 in child_1.get('children'):
                new_child_2 = Node(boiler_id=boiler_id,
                                   parent_id=new_child_1.id,
                                   index=child_2.get('index'),
                                   node_name=child_2.get('node_name'),
                                   id = current_id
                                   )
                db.session.add(new_child_2)
                current_id += 1

                elements = int(child_2.get("Elements"))
                points = int(child_2.get("Points"))

                for element in range(1, elements + 1):
                    for point in range(1, points + 1):
                        new_point = Node(boiler_id=boiler_id,
                                         parent_id=new_child_2.id,
                                         index=point,
                                         node_name='Element ' + str(element) + ' Point ' + str(point),
                                         id = current_id
                                         )
                        db.session.add(new_point)
                        new_point_norm = Norm(node_id=current_id,
                                              default=6.5,
                                              minor=6.0,
                                              major=5.2,
                                              defect=4.5)
                        db.session.add(new_point_norm)

                        current_id += 1
    db.session.commit()











