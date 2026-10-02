from ckan import plugins
from ckan.plugins import toolkit

from ckanext.citations import cli, model
from ckanext.citations.lib.helpers import citations_get_stats


class CitationsPlugin(plugins.SingletonPlugin):
    """Citation tracking (cited-by via OpenAlex/DataCite Event Data),
    dataset disruption index and per-researcher S-index, displayed on the
    dataset page. See README for the architecture (dedicated tables, no
    package_extra/Solr writes) and the v1 scope (FAIR/FUJI scoring is
    explicitly out of scope for now).
    """

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IClick)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        # Touching model.* at load time registers the SQLAlchemy mappings
        # with ckan.model.meta before anything queries them.
        _ = model

    # ITemplateHelpers

    def get_helpers(self):
        return {'citations_get_stats': citations_get_stats}

    # IClick

    def get_commands(self):
        return cli.get_commands()
