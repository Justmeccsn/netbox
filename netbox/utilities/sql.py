from __future__ import unicode_literals

from django.db import connections, models
from django.db.models.sql.compiler import SQLCompiler


class NullsFirstSQLCompiler(SQLCompiler):

    def get_order_by(self):
        result = super(NullsFirstSQLCompiler, self).get_order_by()
        if result:
            return [(expr, (sql + ' NULLS FIRST', params, is_ref)) for (expr, (sql, params, is_ref)) in result]
        return result


class NullsFirstQuery(models.sql.query.Query):

    def get_compiler(self, using=None, connection=None):
        if using is None and connection is None:
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        return NullsFirstSQLCompiler(self, connection, using)


class NullsFirstQuerySet(models.QuerySet):
    """
    Override PostgreSQL's default behavior of ordering NULLs last. This is needed e.g. to order Prefixes in the global
    table before those assigned to a VRF.
    """

    def __init__(self, model=None, query=None, using=None, hints=None):
        super(NullsFirstQuerySet, self).__init__(model, query, using, hints)
        self.query = query or NullsFirstQuery(self.model)


class ObjectFilterQuerySet(models.QuerySet):
    def filter_access(self, user):
        if not user.is_superuser:
            try:
                return self.filter(
                    models.Q(tenant__group__access_group__user=user) |
                    models.Q(tenant__group__access_users=user)
                )
            except TypeError:
                return self.none()
        return self


class NaturalOrderByQuerySet(models.QuerySet):

    def natural_order_by(self, *fields):
        """
        Attempt to order records naturally by segmenting a field into three parts:

        1. Leading integer (if any)
        2. Middle portion
        3. Trailing integer (if any)

        :param fields: The fields on which to order the queryset. The last field in the list will be ordered naturally.
        """
        db_table = self.model._meta.db_table
        primary_field = fields[-1]

        id1 = '_{}_{}1'.format(db_table, primary_field)
        id2 = '_{}_{}2'.format(db_table, primary_field)
        id3 = '_{}_{}3'.format(db_table, primary_field)

        queryset = self.extra(select={
            id1: "CAST(SUBSTRING({}.{} FROM '^(\d{{1,9}})') AS integer)".format(db_table, primary_field),
            id2: "SUBSTRING({}.{} FROM '^\d*(.*?)\d*$')".format(db_table, primary_field),
            id3: "CAST(SUBSTRING({}.{} FROM '(\d{{1,9}})$') AS integer)".format(db_table, primary_field),
        })

        ordering = fields[0:-1] + (id1, id2, id3)

        return queryset.order_by(*ordering)


class FilterNaturalOrderByQuerySet(ObjectFilterQuerySet, NaturalOrderByQuerySet):
    pass
