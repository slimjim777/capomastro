# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Archive.username'
        db.alter_column(u'archives_archive', 'username', self.gf('django.db.models.fields.CharField')(max_length=64, null=True))

        # Changing field 'Archive.host'
        db.alter_column(u'archives_archive', 'host', self.gf('django.db.models.fields.CharField')(max_length=64, null=True))

        # Changing field 'Archive.ssh_credentials'
        db.alter_column(u'archives_archive', 'ssh_credentials_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['credentials.SshKeyPair'], null=True))

    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Archive.username'
        raise RuntimeError("Cannot reverse this migration. 'Archive.username' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Archive.username'
        db.alter_column(u'archives_archive', 'username', self.gf('django.db.models.fields.CharField')(max_length=64))

        # User chose to not deal with backwards NULL issues for 'Archive.host'
        raise RuntimeError("Cannot reverse this migration. 'Archive.host' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Archive.host'
        db.alter_column(u'archives_archive', 'host', self.gf('django.db.models.fields.CharField')(max_length=64))

        # User chose to not deal with backwards NULL issues for 'Archive.ssh_credentials'
        raise RuntimeError("Cannot reverse this migration. 'Archive.ssh_credentials' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'Archive.ssh_credentials'
        db.alter_column(u'archives_archive', 'ssh_credentials_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['credentials.SshKeyPair']))

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
            'artifact': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.Artifact']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
            'duration': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jenkins.Job']"}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'phase': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'jenkins.jenkinsserver': {
            'Meta': {'object_name': 'JenkinsServer'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'remote_addr': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
        }
    }

    complete_apps = ['archives']