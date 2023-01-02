"""
Copyright (c) 2022 Alexander Forselius

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from django.db import models

from django.conf import timezone

from datetime import datetime

import pickle

import uuid

import hashlib
from base64 import b64encode

import pybase62


class Node(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    deleted = models.DateTimeField(null=True, blank=True)

    def get_identifier(self):
        """
        Returns a base62 string representation of the node's ID
        """
        return pybase62.encode(int(self.id))

    def to_dict(self, *args, **kwargs):
        obj = dict(
            id=self.get_identifier(),
            type=self._model._meta.model_name,
            created=datetime.timestamp(self.created),
            updated=datetime.timestamp(self.udated),
            deleted=datetime.timestamp(self.deleted)
        )
        return obj

    class Meta:
        abstract = True


class Chain(Node):
    app_name = models.CharField(max_length=255)
    last_block = models.ForeignKey('Block', on_delete=models.CASCADE, blank=True, null=True)
    genesis = models.ForeignKey('Block', on_delete=models.CASCADE, blank=True, null=True)

    def mint(self, block):
        block.chain = self
        block.save(minting=True)

    def mine_new_block(self):
        """
        Find new operations that haven't been recorded in the chain. These
        operations block id is NULL.
        """
        parent = self.last_block

        block = Block(
            parent=parent
        )
        block.save()
        if not parent:
            self.genesis = block
            self.save()
        
        operations = Operation.objects.filter(
            app_name=self.app_name,
            block__isnull=True,
        ).order_by('created')
        for operation in operations:
            block.record_operation(operation)
        
        self.mint(block)                


class Block(Node):
    """
    Represents a block of a chain, the uuid4 of this block 
    should be an uuid4 that represents the hash value of the block
    """

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    hash = models.UUIDField(null=True, blank=True)
    header = models.JSONField(default={})
    data = models.JSONField(default={})
    minted = models.DateTimeField(null=True, blank=True)
    chain = models.ForeignKey(Chain, on_delete=models.CASCADE, null=True, blank=True)

    def generate_hash(self):
        bin_header = pickle.dumps(self.to_dict()).encode('base64', 'strict')
        hash = hashlib.sha256(bin_header)
        return uuid.uuid4(hash.hexdigest()[::3])

    def delete(self, *args, **kwargs):
        raise Exception("Blocks are immutable and can't be deleted")

    def save(self, *args, **kwargs):
        if self.minted and not 'minting' in kwargs:
            raise Exception("Blocks are immutable")
        self.hash = self.generate_hash()
        super(Block, self).save(*args, **kwargs)

    def to_dict(self, *args, **kwargs):
        obj = super(Block, self).to_dict(*args, **kwargs)
        obj['header'] = self.header,
        obj['data'] = self.data
        return obj

    def record_operation(self, operation):
        if self.minted:
            raise Exception("Cant record on minted block")

class Operation(Node):
    """
    Represents an logged operation which represents 
    the Django-chain event sourcing system, which will 
    be stored in the blockchain.
    """
    model = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    node_id = models.UUIDField()
    values = models.JSONField()
    conditions = models.JSONField()
    block = models.ForeignKey(Block, on_delete=models.CASCADE, null=True, blank=True)
    app_name = models.CharField(max_length=255)
    recorded = models.DateTimeField(null=True, blank=True)

    def to_dict(self, *args, **kwargs):
        return dict(
            type='operation',
            id=self.get_identifier(),
            model=self.model,
            action=self.action,
            node_id=pybase62.encode(self.node_id),
            values=self.values,
            conditions=self.conditions,
            app_name=self.app_name,
            block=self.block,
            recorded=datetime.timestamp(self.recorded)
        )

    def to_sql(self):
        """
        Function removed because I realized this was not a good practice,
        instead execute sql through parameterized insertion by reading values, conditions, model and action
        fields
        """
        raise Exception("No longer used")

    def __str__(self) -> str:
        return self.to_sql()

    def delete(self, *args, **kwargs):
        raise Exception("Blocks are immutable and can't be deleted")

    def save(self, *args, **kwargs):
        if kwargs['created']:
            raise Exception("Blocks are immutable")


class ChainedNode(Node):
    """
    Models that subclass this class will be traced by 
    djangochain.
    The primary key of these models must always be an
    id attribute of type uuid4
    """
