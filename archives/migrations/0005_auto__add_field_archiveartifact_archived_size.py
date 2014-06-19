# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ArchiveArtifact.archived_size'
        db.add_column(u'archives_archiveartifact', 'archived_size',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ArchiveArtifact.archived_size'
        db.delete_column(u'archives_archiveartifact', 'archived_size')


    models = {
        u'archives.archive': {
            'Meta': {'object_name': 'Archive'},
            'basedir': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'policy': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '64'}),
            'ssh_credentials': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['credentials.SshKeyPair']", 'null': 'True', 'blank': 'True'}),
            'transport': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'})
        },
        u'archives.archiveartifact': {
            'Meta': {'object_name': 'ArchiveArtifact'},
            'archive': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['archives.Archive']"}),
            'archived_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'archived_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'archived_size': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'artifact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.Artifact']"}),
            'build': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.Build']", 'null': 'True', 'blank': 'True'}),
            'dependency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['projects.Dependency']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'projectbuild_dependency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['projects.ProjectBuildDependency']", 'null': 'True', 'blank': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'credentials.sshkeypair': {
            'Meta': {'object_name': 'SshKeyPair'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'private_key': ('django.db.models.fields.TextField', [], {}),
            'public_key': ('django.db.models.fields.TextField', [], {})
        },
        u'jenkins.artifact': {
            'Meta': {'object_name': 'Artifact'},
            'build': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.Build']"}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'jenkins.build': {
            'Meta': {'ordering': "['-number']", 'object_name': 'Build'},
            'build_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'console_log': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.Job']"}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'parameters': ('jenkins.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'phase': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'jenkins.jenkinsserver': {
            'Meta': {'object_name': 'JenkinsServer'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'jenkins.job': {
            'Meta': {'unique_together': "(('server', 'name'),)", 'object_name': 'Job'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jobtype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.JobType']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.JenkinsServer']"})
        },
        u'jenkins.jobtype': {
            'Meta': {'object_name': 'JobType'},
            'config_xml': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'projects.dependency': {
            'Meta': {'object_name': 'Dependency'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.Job']", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'parameters': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'projects.project': {
            'Meta': {'object_name': 'Project'},
            'dependencies': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['projects.Dependency']", 'through': u"orm['projects.ProjectDependency']", 'symmetrical': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'projects.projectbuild': {
            'Meta': {'object_name': 'ProjectBuild'},
            'archived': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'build_dependencies': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['jenkins.Build']", 'through': u"orm['projects.ProjectBuildDependency']", 'symmetrical': 'False'}),
            'build_id': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'build_key': ('django.db.models.fields.CharField', [], {'default': "'2d2575e5415b4e69acb98552b81348ff'", 'max_length': '32'}),
            'ended_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phase': ('django.db.models.fields.CharField', [], {'default': "'UNKNOWN'", 'max_length': '25'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['projects.Project']"}),
            'requested_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'requested_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'UNKNOWN'", 'max_length': '10'})
        },
        u'projects.projectbuilddependency': {
            'Meta': {'object_name': 'ProjectBuildDependency'},
            'build': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'projectbuild_dependencies'", 'null': 'True', 'to': u"orm['jenkins.Build']"}),
            'dependency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['projects.Dependency']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'projectbuild': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dependencies'", 'to': u"orm['projects.ProjectBuild']"})
        },
        u'projects.projectdependency': {
            'Meta': {'object_name': 'ProjectDependency'},
            'auto_track': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'current_build': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.Build']", 'null': 'True'}),
            'dependency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['projects.Dependency']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['projects.Project']"})
        }
    }

    complete_apps = ['archives']