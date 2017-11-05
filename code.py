#!/usr/bin/python
#encoding:utf-8
import web

render = web.template.render('templates/')

#url和类的对应关系
urls = (
    '/', 'index',
    '/repo_path', 'repo_path',
    '/add_repo_path', 'add_repo_path',
    '/repo_path_exist', 'repo_path_exist',
    '/compose_path', 'compose_path',
    '/add_repo_path_exist', 'add_repo_path_exist',
    '/repository_group', 'repository_group',
    '/search_group', 'search_group',
    '/group', 'group',
    '/repository_authz', 'repository_authz',
    '/search_authz', 'search_authz',
    '/authz', 'authz',
    '/user', 'user',
    '/add_user', 'add_user',
    '/repository_groupmembership', 'repository_groupmembership',
    '/list_user_group', 'list_user_group',
    '/add_user_into_group', 'add_user_into_group',
    '/pa55w0rd', 'pa55w0rd',
    '/choose_user', 'choose_user',
    '/user_group', 'user_group',
    '/choose_repo', 'choose_repo',
    '/choose_group', 'choose_group',
    '/group_user', 'group_user',
)

#连接数据库
db  = web.database(dbn='mysql', user='root', pw='omproot', host='localhost', port=3306, db='svn_aa', charset='utf8', use_unicode=0)

class index:
    def GET(self):
        #打开index.html，这里面有做各个操作的链接
        return render.index()

class repo_path:
    def GET(self):
        #打开repo_path.html，将在这里填入repository名和希望创建的目录名
        return render.repo_path("", -1)

class add_repo_path:
    def POST(self):
        #获取提交的表单中所有输入
        formInput = web.input() 
        #把unicode的值转化成能识别的值
        repo_name = formInput.repo_name.encode('ascii')
        repo_name_zh = formInput.repo_name_zh.encode('utf-8')
        #把输入的若干用逗号连起来的path分开来存入list里
        pathsList = formInput.paths.encode("ascii").split(",")

        #把repository英文名和中文名插入到svn_repository表中
        queryRepositoryStr = "INSERT INTO svn_repository (name, repo_name) VALUES ('" + repo_name + "', '" + repo_name_zh + "');"
        db.query(queryRepositoryStr)

        #把刚才插入的repository id取出来备用
        queryRepositoryStr = "SELECT id FROM svn_repository WHERE name='" + repo_name + "';"
        id = db.query(queryRepositoryStr)
        repoId = str(id[0].id)

        #把repository的根目录插入svn_repopath表中
        queryStr = "INSERT INTO svn_repopath (repository_id, path) VALUES (" + repoId + ", '/');"
        #从存有path的list里把path取出来，去空格，如果为空字符串不处理，把有意义的目录插入到svn_repopath表中
        for path in pathsList:
            pathAfterTrim = path.strip()
            if cmp(pathAfterTrim, "") != 0:
                queryStr = queryStr + " INSERT INTO svn_repopath (repository_id, path) VALUES (" + repoId + ", '/" + pathAfterTrim + "');"
        #因为一次有很多sql语句提交，用下面的方式处理sql事务
        dbTrans = DbTransaction()
        dbTrans.execute(queryStr)
        #打开含有返回首页链接的网页
        return render.back_home()

class repo_path_exist:
    def GET(self):
        #查询出id>11的repository，因为id<=11的repository已经不被使用了
        queryRepositoryStr = "SELECT * FROM svn_repository WHERE id>11;"
        repos = db.query(queryRepositoryStr)
        #打开选择repository的网页
        return render.lsrepo(repos, "pathexist")

class compose_path:
    def POST(self):
        formInput = web.input()
        repoId = formInput.repository
        #把需要添加文件夹路径的repository找出来
        queryRepositoryStr = "SELECT name FROM svn_repository WHERE id=" + repoId + ";"
        name = db.query(queryRepositoryStr)

        #打开repo_path.html，将在这里填入希望创建的目录名
        return render.repo_path(name[0].name, repoId)

class add_repo_path_exist:
    def POST(self):
        #获取提交的表单中所有输入
        formInput = web.input() 

        repoId = formInput.repoId
        #把输入的若干用逗号连起来的path分开来存入list里
        pathsList = formInput.paths.encode("ascii").split(",")

        queryStrList = []
        #从存有path的list里把path取出来，去空格，如果为空字符串不处理，把有意义的目录插入到svn_repopath表中
        for path in pathsList:
            pathAfterTrim = path.strip()
            if cmp(pathAfterTrim, "") != 0:
                queryStrList.append("INSERT INTO svn_repopath (repository_id, path) VALUES (" + repoId + ", '/" + pathAfterTrim + "');")
        #把list里的sql语句字符串之间加上空格拼成一个大的字符串
        queryStr = " ".join(queryStrList)
        #因为一次有很多sql语句提交，用下面的方式处理sql事务
        dbTrans = DbTransaction()
        dbTrans.execute(queryStr)
        #打开含有返回首页链接的网页
        return render.back_home()

class repository_group:
    def GET(self):
        #查询出id>11的repository，因为id<=11的repository已经不被使用了
        queryRepositoryStr = "SELECT * FROM svn_repository WHERE id>11;"
        repos = db.query(queryRepositoryStr)
        #打开选择repository的网页
        return render.lsrepo(repos, "group")

class search_group:
    def POST(self):
        formInput = web.input()
        repoId = formInput.repository
        #把需要添加权限组的repository找出来
        queryRepositoryStr = "SELECT name FROM svn_repository WHERE id=" + repoId + ";"
        name = db.query(queryRepositoryStr)
        #把repository的name传到输入新添加的权限组名字的页面
        return render.mkgroup(name[0].name)

class group:
    def POST(self):
        groups = web.input()
        #把输入的若干用逗号连起来的权限组名分开来存入list里
        groupsList = groups.groups.encode("ascii").split(",")
        
        #为了在添加group_all组的时候，自动把管理员也加入该group_all组，所以这里设一个判断是否添加管理员进入group_all的标识变量，设一个可能会用来存储group_all组名的变量
        isAddAdminToGroupAll = False
        groupAllName = ""

        queryStrList = []
        #从存有权限组名的list里把group取出来，去空格，如果为空字符串不处理，把有意义的权限组插入到svn_group表中
        for group in groupsList:
            groupAfterTrim = group.strip()
            if cmp(groupAfterTrim, "") != 0:
                #如果添加的权限组包含group_all组，把标识变量置为True，把权限组名存在后续要用到的group_all组名变量里
                if groupAfterTrim.find('group_all') != -1:
                    isAddAdminToGroupAll = True
                    groupAllName = groupAfterTrim
                queryStrList.append("INSERT INTO svn_group (name) VALUES ('" + groupAfterTrim + "');") 
        #把list里的sql语句字符串之间加上空格拼成一个大的字符串
        queryStr = " ".join(queryStrList)
        #因为一次有很多sql语句提交，用下面的方式处理sql事务
        dbTrans = DbTransaction()
        dbTrans.execute(queryStr)

        #如果标识变量为True，把刚才创建的group_all组的id查出来，并把管理员id和group_all组的id插入到svn_groupmembership表中
        if isAddAdminToGroupAll:
           groupAllId = db.query("SELECT id FROM svn_group WHERE name='" + groupAllName + "';")
           db.query("INSERT INTO svn_groupmembership (`user_id`, `group_id`) VALUES (114, " + str(groupAllId[0].id) + ");")

        #打开含有返回首页链接的网页
        return render.back_home()

class repository_authz:
    def GET(self):
        #查询出id>11的repository，因为id<=11的repository已经不被使用了
        queryRepositoryStr = "SELECT * FROM svn_repository WHERE id>11"
        repos = db.query(queryRepositoryStr)
        #打开选择repository的网页
        return render.lsrepo(repos, "authz")

class search_authz:
    def POST(self):
        formInput = web.input()
        repoId = formInput.repository
        #把需要给权限组赋权的repository找出来
        queryRepositoryStr = "SELECT name FROM svn_repository WHERE id=" + repoId
        name = db.query(queryRepositoryStr)

        #把属于所有这个repository的权限组找出来
        queryGroupStr = "SELECT * FROM svn_group WHERE name LIKE '%" + name[0].name + "_group%'"
        groups = db.query(queryGroupStr)
        #把结果集转成list，如果不是list类型，迭代类型的结果集只能使用一次，而在后面的网页里需多次使用这个list
        groupList = list(groups)
        #把group列表里的首个元素取出来，这是拥有所有权限的组名
        group_all = groupList[0]
        #把group列表里除首个元素之外的其它元素重新赋给这个list
        groupListLength = len(groupList)
        groupList = groupList[1:groupListLength]

        #把属于所有这个repository的path找出来
        queryRepoPathStr = "SELECT * FROM svn_repopath WHERE repository_id=" + repoId
        repoPaths = db.query(queryRepoPathStr)

        #把结果集转成list，如果不是list类型，迭代类型的结果集只能使用一次，而在后面的网页里需多次使用这个list
        repoPathList = list(repoPaths)
        #把path列表里的首个元素取出来，这是根目录
        repoPathRoot = repoPathList[0]
        #把path列表里除首个元素之外的其它元素重新赋给这个list
        repoPathListLength = len(repoPathList)
        repoPathList = repoPathList[1:repoPathListLength]
        #把拥有所有权限的组名，其它权限组列表，根目录，其它目录列表传入到assign.html页面
        return render.assign(group_all, groupList, repoPathRoot, repoPathList)

class authz:
    def POST(self):
        #获取表单里的数据，并把所有name是rwbox的元素组成一个列表，把所有name是rwbox_all的元素组成一个列表
        formInput = web.input(rwbox=[], rwbox_all=[])

        rootPermission = formInput.rwbox_root
        permissionList = formInput.rwbox
        permissionAllList = formInput.rwbox_all

        #把传入的根权限的信息字符串：all 拥有所有权限的组id 根目录id，按之间的空格分开存入list中
        rootPermissionStr = rootPermission.encode("ascii").split(" ")

        permissionStrList = []
        permissionAllStrList = []
        
        #把真实的读写权限从权限列表中取出并放入list中
        for permissionItem in permissionList:
            permissionStrList.append(permissionItem.encode("ascii"))
        #把所有的读写权限从权限列表中取出并放入list中
        for permissionAllItem in permissionAllList:
            permissionAllStrList.append(permissionAllItem.encode("ascii"))
        #permissionAllStrList为全集，permissionStrList为子集，通过下面的算法取出补集，原因是在设权限的时候，需要对某个组设它这个组对其它目录的不可读或不可写权限，取出的补集就是某个组对其它目录的不可读或不可写的权限记录
        for permissionStr in permissionStrList:
            count = permissionAllStrList.count(permissionStr) 
            if count == 1:
                permissionAllStrList.remove(permissionStr)

        queryStrList = []
        #插入拥有所有权限的组对根目录的可读可写权限进入svn_grouppermission
        queryStrList.append("INSERT INTO svn_grouppermission (`group_id`, `repository_path_id`, `read`, `write`, `recursive`) VALUES (" + rootPermissionStr[1] +", " + rootPermissionStr[2] + ", 1, 1, 1);")
        
        group_repoPath = ""
        #permissionAllStr对同一个组和同一个路径的读和写权限是分开描述的，而sql语句里同一个组和同一个路径的读写权限是一句sql，因此在判断时，先把组和路径拼成一个临时字符串，然后按描述的read或者write拼一条这个组对这个路径的不可读或不可写的sql语句，如果list里下一个项目描述的权限仍旧是针对这个组和路径的权限，那么可以肯定，这个权限组对这个路径既没有读权限也没有写权限，那么直接把上一个sql语句删掉，加一条对相应路径不可读不可写的sql语句
        for permissionAllStr in permissionAllStrList:
            permissionAllStr = permissionAllStr.split(" ")
            tempStr = permissionAllStr[1] + permissionAllStr[2]
            if cmp(group_repoPath, tempStr) != 0:
                group_repoPath = tempStr 
                if cmp("read", permissionAllStr[0]) == 0:
                    queryStrList.append("INSERT INTO svn_grouppermission (`group_id`, `repository_path_id`, `read`, `write`, `recursive`) VALUES (" + permissionAllStr[1] +", " + permissionAllStr[2] + ", 0, 1, 1);")
                else:
                    queryStrList.append("INSERT INTO svn_grouppermission (`group_id`, `repository_path_id`, `read`, `write`, `recursive`) VALUES (" + permissionAllStr[1] +", " + permissionAllStr[2] + ", 1, 0, 1);")
            else:
                queryStrList.pop()
                queryStrList.append("INSERT INTO svn_grouppermission (`group_id`, `repository_path_id`, `read`, `write`, `recursive`) VALUES (" + permissionAllStr[1] +", " + permissionAllStr[2] + ", 0, 0, 1);")
        #把list里的sql语句字符串之间加上空格拼成一个大的字符串
        queryStr = " ".join(queryStrList)
        #因为一次有很多sql语句提交，用下面的方式处理sql事务
        dbTrans = DbTransaction()
        dbTrans.execute(queryStr)
        #打开含有返回首页链接的网页
        return render.back_home()

class user:
    def GET(self):
        #打开user.html，将在这里填入user名、密码和中文名
        return render.user()

class add_user:
    def POST(self):
        try:
            #获取提交的表单中所有输入
            formInput = web.input() 
            #把unicode的值转化成能识别的值
            #把输入的若干用分号连起来的user分开来存入list里
            usersList = formInput.users.encode("utf-8").split(";")
            queryStrList = []
            #把每个用户信息再以冒号分开，去掉空格，并组成sql语句准备插入到svn_user表中
            for user in usersList:
                #只有分号分隔出来的内容不全是空格的时候才去处理它。如果内容不全是空格，去掉空格后长度不会等于0 
                if len(user.strip()) != 0:
                    userAttrList = user.split(":")
                    if len(userAttrList) != 3:
                        print "错误：输入的用户信息格式有误，分了不到或不止3个域"
                        sys.exit()
                    queryStrList.append("INSERT INTO svn_user (name, pass, name_real) VALUES ('" + userAttrList[0].strip() + "', '" + userAttrList[1].strip() + "', '" + userAttrList[2].strip() + "');")
                #把list里的sql语句字符串之间加上空格拼成一个大的字符串
                queryStr = " ".join(queryStrList)
        except SystemExit:
            print "System Exit due to an error!"
        except:
            traceback.print_exc()

        #因为一次有很多sql语句提交，用下面的方式处理sql事务
        dbTrans = DbTransaction()
        dbTrans.execute(queryStr)
        #打开含有返回首页链接的网页
        return render.back_home()
            
class repository_groupmembership:
    def GET(self):
        #查询出id>11的repository，因为id<=11的repository已经不被使用了
        queryRepositoryStr = "SELECT * FROM svn_repository WHERE id>11"
        repos = db.query(queryRepositoryStr)
        #打开选择repository的网页
        return render.lsrepo(repos, "groupmembership")

class list_user_group:
    def POST(self):
        formInput = web.input()
        repoId = formInput.repository
        #根据repository id把repository name反查出来
        queryRepositoryStr = "SELECT name FROM svn_repository WHERE id=" + repoId + ";"
        name = db.query(queryRepositoryStr)
        #把需要添加用户的权限组找出来
        queryGroupStr = "SELECT * FROM svn_group WHERE name LIKE '%" + name[0].name + "_group%' ORDER BY name"
        groups = db.query(queryGroupStr)
        #把所有的用户都列出来
        queryUserStr = "SELECT * FROM svn_user ORDER BY name"
        users = db.query(queryUserStr)
        #把用户和找出来的权限组传到设置用户和权限组对应关系的页面
        return render.mkgroupmembership(users, groups)

class add_user_into_group:
    def POST(self):
        #获取表单里的数据，并把所有name是user的元素组成一个列表
        formInput = web.input(user=[], group=[])


        userList = formInput.user
        groupList = formInput.group

        queryStrList = []
        #把用户与权限组的对应关系插入svn_groupmembership
        for group in groupList:
            for user in userList:
                queryStrList.append("INSERT INTO svn_groupmembership (`user_id`, `group_id`) VALUES (" + user + ", " + group + ");")
        
        #把list里的sql语句字符串之间加上空格拼成一个大的字符串
        queryStr = " ".join(queryStrList)

        #因为一次有很多sql语句提交，用下面的方式处理sql事务
        dbTrans = DbTransaction()
        dbTrans.execute(queryStr)
        #打开含有返回首页链接的网页
        return render.back_home()

class pa55w0rd:
    def GET(self):
        #查询所有用户
        queryUserStr = "SELECT * FROM svn_user;"
        users = db.query(queryUserStr)
        userList = []
        #svn_user表的一个字段名叫pass，由于pass是python保留字，在网页里没法取出pass对应的value，所以在这里预处理一下，把name和pass从查询的结果集中取出来，最后做一个元素是字典的列表传给网页
        for user in users:
            #把结果集的数据强制转换成字符串
            userStr = str(user)
            nameIndex = userStr.index("'name'")
            passIndex = userStr.index("'pass'")
            rightBraceIndex = userStr.index("}")
            name = userStr[nameIndex + 9 : passIndex - 3]
            password = userStr[passIndex + 9 : rightBraceIndex - 1]
            #把结果集中的pass对应的数据以password为key存储起来，这样网页中就能取出来使用了
            userDict = {"name" : name , "password" : password}
            userList.append(userDict) 
        #打开列出所有用户名密码的网页
        return render.lsuser(userList)

class choose_user:
    def GET(self):
        #查询所有用户
        queryUserStr = "SELECT * FROM svn_user ORDER BY name;"
        users = db.query(queryUserStr)
        #打开选择用户的网页
        return render.chooseuser(users)

class user_group:
    def POST(self):
        #获取表单里的数据，并把所有name是user的元素组成一个列表
        formInput = web.input(user=[])
        userIdList = formInput.user

        #准备两个列表，一个放入用户名，一个放入每个用户所属的权限组列表
        userNameList = []
        groupsList = []
        for userId in userIdList:
            #根据user id查出该用户记录
            userResultSet = db.query("SELECT * FROM svn_user WHERE id = " + userId + ";")
            #由于user id的唯一性所以结果集中只可能包含一条记录
            user = userResultSet[0]
            #如果用户有中文名就把中文名装进用户名列表，如果没有中文名就把name放入用户名列表
            name_real = user.name_real
            if name_real == "" or name_real is None:
                userNameList.append(user.name)
            else:
                userNameList.append(name_real)
            #为单个用户所属的所有权限组准备一个列表
            groupList = []
            #根据user id查出用户都属于哪些权限组
            groupmemberships = db.query("SELECT * FROM svn_groupmembership WHERE user_id = " + userId + ";")
            #把用户所属的权限组的记录一条条取出，如果权限组id<29不加入权限组列表，因为小于29的权限组已经没有意义
            for groupmembership in groupmemberships:
                groupId = groupmembership.group_id
                if groupId > 29:
                    #根据权限组id从svn_group表中查询出权限组记录
                    groupNameResultSet = db.query("SELECT name FROM svn_group WHERE id = " + str(groupId) + ";")
                    #由于group id的唯一性所以结果集中只可能包含一条记录，取出该记录的name放入权限组列表
                    groupList.append(groupNameResultSet[0].name)
            #给这个权限组列表中的权限组按字母排序，这样到网页中显示出来直观整齐
            groupList.sort()
            #把每个用户的权限组列表再加入到最开始准备的列表里
            groupsList.append(groupList)
        
        #打开用户所属的权限组的网页
        return render.usergroup(userNameList, groupsList)

class choose_repo:
    def GET(self):
        #查询出id>11的repository，因为id<=11的repository已经不被使用了
        queryRepositoryStr = "SELECT * FROM svn_repository WHERE id>11;"
        repos = db.query(queryRepositoryStr)
        #打开选择repository的网页
        return render.lsrepo(repos, "chooserepo")

class choose_group:
    def POST(self):
        #获取表单里的数据
        formInput = web.input()
        repoId = formInput.repository
        #根据repo id查出repo名
        queryRepoNameStr = "SELECT name FROM svn_repository WHERE id = " + repoId + ";"
        repoNameStr = db.query(queryRepoNameStr)
        #查出该repo所有的权限组
        queryGroupStr = "SELECT * FROM svn_group WHERE name LIKE '%" + repoNameStr[0].name + "_group_%' ORDER BY name"
        groupList = db.query(queryGroupStr)
        return render.choosegroup(groupList)

class group_user:
    def POST(self):
        #获取表单里的数据，并把所有name是group的元素组成一个列表
        formInput = web.input(group=[])
        groupIdList = formInput.group

        #准备两个列表，一个放入权限组名，一个放入每个权限组包含的用户列表
        groupNameList = []
        usersList = []

        for groupId in groupIdList:
            #根据group id查出该权限组记录
            groupNameResultSet = db.query("SELECT name FROM svn_group WHERE id = " + groupId + ";")
            #由于group id的唯一性所以结果集中只可能包含一条记录
            groupName = groupNameResultSet[0].name
            groupNameList.append(groupName)
            #为单个权限组包含的用户准备一个列表
            userList = []
            #根据group id查出权限组都包含哪些用户
            groupmemberships = db.query("SELECT * FROM svn_groupmembership WHERE group_id = " + groupId + ";")
            #把权限组包含的用户的记录一条条取出
            for groupmembership in groupmemberships:
                userId = groupmembership.user_id
                #根据user id从svn_user表中查询出用户记录
                userResultSet = db.query("SELECT * FROM svn_user WHERE id = " + str(userId) + ";")
                user = userResultSet[0] 
                #有中文名的把中文名放入用户列表，没有中文名把name放入用户列表
                name_real = user.name_real
                if name_real == "" or name_real is None:
                    userList.append(user.name)
                else:
                    userList.append(name_real)
            #给列表里的用户排序
            userList.sort()
            #把每个权限组包含的用户列表再加入到最开始准备的列表里
            usersList.append(userList)

        #打开权限组包含的用户的网页
        return render.groupuser(groupNameList, usersList)

class DbTransaction:
    def execute(self, queryStr):
        t = db.transaction()
        try:
            db.query(queryStr)
        except:
            t.rollback()
            print "数据库操作有异常，已回滚"
            traceback.print_exc()
            raise
        else:
            t.commit()
        
if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()
