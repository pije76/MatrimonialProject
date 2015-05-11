# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations
def diff_in_years(born):
            today=request.now
            return today.year-born.year-((today.month,today.day)<(born.month,born.day))

def index():
    if auth.user:
        #db.auth_user[auth.user.id]=dict(age=diff_in_years(auth.user.DOB))
        redirect(URL('user/profile'))
    else:
        redirect(URL('user/login'))
    return dict()

def notfound():
    return dict()

def req():
    a = request.args[0]
    b = db((db.details.send==auth.user.id) & (db.details.rec==a)).select()
    session.flash = "You already sent a request"
    if len(b)!=0: redirect(URL('default/view_user', a))
    db.details.insert(send=auth.user.id, rec=a, accepted=False)
    session.flash = "Request sent!"
    redirect(URL('default/view_user', a))
    return

def acc():
    a = request.args[0]
    db((db.details.rec==auth.user.id) & (db.details.send==a)).update(accepted=True)
    session.flash = "Request accepted!"
    redirect(URL('friends'))
    return

@auth.requires_login()
def friends():
    b = db((db.details.rec==auth.user.id) & (db.auth_user.id==db.details.send)).select(orderby=~db.details.accepted)
    c = db((db.details.rec==db.auth_user.id) & (db.details.send==auth.user.id)).select()
    return dict(b=b, c=c)

@auth.requires_login()
def lucky():
    if auth.user.sex=="Female":
        sex="Male"
    elif auth.user.sex=="Male":
        sex="Female"
    else:
        sex="Other"
    minimum_age=int(auth.user.age)-10
    maximum_age=int(auth.user.age)+10
    if minimum_age<18: minimum_age=18
    minimum_salary=auth.user.salary.split('-')[0]
    redirect(URL('default', 'result', vars={'sex': sex, 'minimum_age': minimum_age, 'maximum_age': maximum_age, 'minimum_salary': minimum_salary}))
    return

@auth.requires_login()
def search():
    form = crud.create(db.find)
    if(form.process().accepted):
        redirect(URL('default','result',vars=form.vars))
    return dict(form=form)

@auth.requires_login()
def result():
    a= db.auth_user.salary=='0-10,000'
    b= db.auth_user.salary=='10,000-25,000'
    c= db.auth_user.salary=='25,000-50,000'
    d= db.auth_user.salary=='50,000-200,000'
    e= db.auth_user.salary=='200,000+'
    q1 = db.auth_user.sex==request.vars.sex
    q2 = db.auth_user.id != auth.user.id
    amin = db.auth_user.age >= request.vars.minimum_age
    amax = db.auth_user.age <= request.vars.maximum_age
    if request.vars.minimum_salary == '0':
        s= a|b|c|d|e
    elif request.vars.minimum_salary == '10,000':
        s= b|c|d|e
    elif request.vars.minimum_salary == '25,000':
        s= c|d|e
    elif request.vars.minimum_salary == '50,000':
        s=d|e
    elif request.vars.minimum_salary == '200,000':
        s=e
    rows=db(q1 & q2 & amin & amax & s).select()
    return dict(rows=rows)
    #return dict(sex=request.vars.sex)

def view_users():
    dic = db(db.auth_user).select()
    return dict(dic = dic)

@auth.requires_login()
def view_user():
    def diff_in_years(born):
            today=request.now
            return today.year-born.year-((today.month,today.day)<(born.month,born.day))
    user = db(db.auth_user.id == request.args[0]).select()
    send = db.details.send==auth.user.id
    rec = db.details.rec==user[0].id
    q3 = db.details.rec==auth.user.id
    q4 = db.details.send==user[0].id
    acc = db(send&rec | q3&q4).select()
    if len(acc)!=0:
        bec=acc[0]['accepted'] #Whether I can see her contact details
    else:
        bec=-1
    return dict(user = user, ac=bec)

def message():
    db.messages.me.default=auth.user.id
    db.messages.dest.default=request.args[0]
    db.messages.mname.default=auth.user.first_name
    dn=db(db.auth_user.id==request.args[0]).select()
    per=dn[0]['first_name']
    db.messages.dname.default=per
    db.messages.sent_on.default=request.now
    form=crud.create(db.messages)
    q1=db.messages.me==auth.user.id
    q2=db.messages.dest==request.args[0]
    q3=db.messages.me==request.args[0]
    q4=db.messages.dest==auth.user.id
    prev=db(q1&q2 | q3&q4).select(orderby=db.messages.sent_on,limitby=(0,10))
    return locals()

@auth.requires_login()
def inbox():
    q1=db.messages.dest==auth.user.id
    one=db(q1).select(db.messages.me,db.messages.mname,distinct=True,orderby=db.messages.sent_on)
    return locals()

@auth.requires_login()
def outbox():
    q1=db.messages.me==auth.user.id
    one=db(q1).select(db.messages.dest,db.messages.dname,distinct=True,orderby=db.messages.sent_on)
    return locals()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    if request.args[0]== 'profile':
        if auth.user:
            db.auth_user[auth.user.id]=dict(age=diff_in_years(auth.user.DOB))
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()

def register():
    form = SQLFORM(db.users);
    return dict(form = form)

@auth.requires_login()
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)
