# -*- coding: utf-8 -*-

import util
import datetime
import tornado.web


from model import Relation
from model import Fav
from model import Entry
from model import Comment
from view import BaseHandler


PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class AjaxRelationHandler(BaseHandler):
    @property
    def relation(self): return Relation()

    def _render_error(self, result):
        result["code"] = 404
        self.render("ajax/pubu.json", result=result)

    def post(self):
        result = {"code": 200, "msg": "OK", "end": 0, "html": ""}

        offset = int(self.get_argument("offset", "0"))
        p = int(self.get_argument("p", "1"))
        user_id = self.get_argument("user_id", None)
        filter = self.get_argument("filter", "None")

        if not filter in ("friends", "followers") and user_id:
            self._render_error(result)
            return

        p = 1 if p < 1 else p
        if filter == "friends":
            total = self.relation.get_friends_count(int(user_id))
        else:
            total = self.relation.get_followers_count(int(user_id))

        if total <= 0:
            self._render_error(result)
            return

        tmp = offset
        offset = (p - 1) * MAX_PAGE_SIZE + offset
        limit = PAGE_SIZE

        if filter == "friends":
            users = self.relation.get_friends(int(user_id), offset, limit)
        else:
            users = self.relation.get_followers(int(user_id), offset, limit)

        """Get Relations for the current user."""
        if self.current_user:
            ids = [u["_id"] for u in users]
            ifriends = self.relation.get_relations_by_ids(
                self.current_user["_id"], ids)
            for user in users:
                user["ifollow"] = True if user["_id"] in ifriends else False

        tmp = tmp + len(users)
        htmls = []
        for i in range(0, len(users)):
            args = {'user': users[i], 'odd': True if i % 2 == 0 else False}
            html = self.render_string("modules/person.html", **args)
            htmls.append(util.json_encode(html))
        result["html"] = htmls

        pager = tmp % MAX_PAGE_SIZE == 0
        final = (offset + len(users)) >= total
        if pager: result["end"] = 1
        if final: result["end"] = 2
        self.render("ajax/pubu.json", result=result)


class AjaxUserTopsHandler(BaseHandler):
    @property
    def entry_dal(self): return Entry()

    @property
    def relation_dal(self): return Relation()

    def _render_error(self, result):
        result["code"] = 404
        self.render("ajax/tops.json", result=result)

    def post(self):
        result = {"code": 200, "msg": "OK", "tops": [], "me_follow": 0}
        user_id = self.get_argument("user_id", None)
        limit = int(self.get_argument("limit", "4"))

        if not (user_id and user_id.isdigit()):
            self._render_error(result)
            return
        tops = self.entry_dal.get_user_top_entries(int(user_id), limit)
        result["tops"] = tops

        followed = False
        if self.current_user:
            tmp = self.relation_dal.get_relation(
                self.current_user["_id"], user_id)
            if tmp: followed = True
        result["me_follow"] = 1 if followed else 0

        self.render("ajax/tops.json", result=result)



class AjaxEntryLikerHandler(BaseHandler):
    @property
    def fav_dal(self): return Fav()

    def _render_error(self, result):
        result["code"] = 404
        self.render("ajax/likers.json", result=result)

    def post(self):
        result = {"code": 200, "msg": "OK", "likers": []}
        entry_id = self.get_argument("entry_id", None)
        if not (entry_id and entry_id.isdigit()):
            self._render_error(result)
            return
        likers = self.fav_dal.get_entry_likers(int(entry_id))
        result["likers"] = likers
        self.render("ajax/likers.json", result=result)


class AjaxCommentHandler(BaseHandler):

    @property
    def comment_dal(self): return Comment()

    @property
    def entry_dal(self): return Entry()

    def post(self):
        id = self.get_argument("id", None)
        content = self.get_argument("content", None)
        if not (id and content and self.current_user): return

        page = self.get_argument("page", None)

        user_id = self.current_user["_id"]
        comment = {
            "_id": self.comment_dal.get_id(),
            "user_id": user_id,
            "user": self.comment_dal.dbref("users", user_id),
            "entry_id": int(id),
            "entry": self.comment_dal.dbref("entries", int(id)),
            "content": content,
            "published": datetime.datetime.now()
        }
        cid = self.comment_dal.save(comment)
        self.entry_dal.update_comments_count(int(id))

        comment = self.comment_dal.get({"_id": cid})

        if not page:
            html = self.render_string(
                "modules/mini_comment.html", comment=comment)
        else:
            html = self.render_string(
                "modules/comment.html", comment=comment)
        self.write("{id: %s, html: '%s'}" % (id, util.json_encode(html)))
