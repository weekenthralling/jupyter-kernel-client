from __future__ import annotations

import pprint

import six
from kubernetes.client.configuration import Configuration


class V1KernelSpec:
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {  # noqa: RUF012
        "template": "V1PodTemplateSpec",
    }

    attribute_map = {  # noqa: RUF012
        "template": "template",
    }

    def __init__(
        self,
        template=None,
        local_vars_configuration=None,
    ):
        """V1KernelSpec - a model defined in OpenAPI"""
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._template = None
        self.discriminator = None

        self.template = template

    @property
    def template(self):
        """Gets the template of this V1KernelSpec.  # noqa: E501


        :return: The template of this V1KernelSpec.  # noqa: E501
        :rtype: V1PodTemplateSpec
        """
        return self._template

    @template.setter
    def template(self, template):
        """Sets the template of this V1KernelSpec.


        :param template: The template of this V1KernelSpec.  # noqa: E501
        :type: V1PodTemplateSpec
        """
        if self.local_vars_configuration.client_side_validation and template is None:
            error_msg = "Invalid value for `template`, must not be `None`"
            raise ValueError(error_msg)

        self._template = template

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(  # noqa: C417
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (
                            (item[0], item[1].to_dict())
                            if hasattr(item[1], "to_dict")
                            else item
                        ),
                        value.items(),
                    )
                )
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, V1KernelSpec):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, V1KernelSpec):
            return True

        return self.to_dict() != other.to_dict()