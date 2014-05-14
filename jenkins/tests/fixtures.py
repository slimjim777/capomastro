job_with_parameters = """\
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
         <name>BUILD_ID</name>
         <description>The projectbuild id to associate with.</description>
         <defaultValue></defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>BRANCH_TO_CHECKOUT</name>
          <description>Branch to checkout and build.</description>
          <defaultValue>http:///launchpad.net/mybranch</defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
</project>
"""
