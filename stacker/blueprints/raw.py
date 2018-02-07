"""Blueprint representing raw template module."""

import hashlib

import yaml

from .base import Blueprint
from ..util import get_template_params, get_template_file_format

from ..exceptions import MissingVariable, UnresolvedVariable


def resolve_variable(var_name, var_def, provided_variable, blueprint_name):
    """Resolve a provided variable value against the variable definition.

    This acts as a subset of resolve_variable logic in the base module, leaving
    out everything that doesn't apply to CFN parameters.

    Args:
        var_name (str): The name of the defined variable on a blueprint.
        var_def (dict): A dictionary representing the defined variables
            attributes.
        provided_variable (:class:`stacker.variables.Variable`): The variable
            value provided to the blueprint.
        blueprint_name (str): The name of the blueprint that the variable is
            being applied to.

    Returns:
        object: The resolved variable string value.

    Raises:
        MissingVariable: Raised when a variable with no default is not
            provided a value.
        UnresolvedVariable: Raised when the provided variable is not already
            resolved.

    """
    if provided_variable:
        if not provided_variable.resolved:
            raise UnresolvedVariable(blueprint_name, provided_variable)

        value = provided_variable.value
    else:
        # Variable value not provided, try using the default, if it exists
        # in the definition
        try:
            value = var_def["Default"]
        except KeyError:
            raise MissingVariable(blueprint_name, var_name)

    return value


class RawTemplateBlueprint(Blueprint):  # pylint: disable=abstract-method
    """Blueprint class for blueprints auto-generated from raw templates."""

    def __init__(self, name, context,  # pylint: disable=too-many-arguments
                 raw_template_path, mappings=None, description=None):
        """Add raw_template_path to base blueprint class."""
        super(RawTemplateBlueprint, self).__init__(name,
                                                   context,
                                                   mappings,
                                                   description)
        self._raw_template_path = raw_template_path
        self._raw_template_format = get_template_file_format(raw_template_path)

    def render_template(self):
        """Load template and generate its md5 hash."""
        with open(self.raw_template_path, 'r') as template:
            rendered = template.read()
        version = hashlib.md5(rendered).hexdigest()[:8]
        parsed_template = yaml.load(rendered)
        if 'Transform' in parsed_template:
            self.template.add_transform(parsed_template['Transform'])
        if self.description:
            self.set_template_description(self.description)
        return (version, rendered)

    def get_parameter_definitions(self):
        """Get the parameter definitions to submit to CloudFormation.

        Returns:
            dict: parameter definitions. Keys are parameter names, the values
                are dicts containing key/values for various parameter
                properties.

        """
        return get_template_params(self.raw_template_path)

    def resolve_variables(self, provided_variables):
        """Resolve the values of the blueprint variables.

        This will resolve the values of the template parameters with values
        from the env file, the config, and any lookups resolved.

        Args:
            provided_variables (list of :class:`stacker.variables.Variable`):
                list of provided variables

        """
        self.resolved_variables = {}
        defined_variables = self.get_parameter_definitions()
        variable_dict = dict((var.name, var) for var in provided_variables)
        for var_name, var_def in defined_variables.iteritems():
            value = resolve_variable(
                var_name,
                var_def,
                variable_dict.get(var_name),
                self.name
            )
            self.resolved_variables[var_name] = value

    def get_parameter_values(self):
        """Return a dictionary of variables with `type` :class:`CFNType`.

        Returns:
            dict: variables that need to be submitted as CloudFormation
                Parameters. Will be a dictionary of <parameter name>:
                <parameter value>.

        """
        return self.get_variables()

    def get_required_parameter_definitions(self):
        """Return all template parameters that do not have a default value.

        Returns:
            dict: dict of required CloudFormation Parameters for the blueprint.
                Will be a dictionary of <parameter name>: <parameter
                attributes>.

        """
        required = {}
        for i in list(self.get_parameter_definitions().items()):
            if i[1].get('Default', None) is None:
                required[i[0]] = i[1]
        return required

    @property
    def raw_template_format(self):
        """Return raw_template_format."""
        return self._raw_template_format

    @property
    def raw_template_path(self):
        """Return raw_template_path."""
        return self._raw_template_path
