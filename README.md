# Djangochain

WIP.

An experiment with a concept of a decentralized kind of django project by emulating blockchain behavior by recording events in a set of database table, for replicating changes to other instances of the same django project installation (peers).

This project primary targets Django 4 and PostgreSQL database backend.

It is not intended for production use, it is only a demo and experiment.

# How the decentralized django app are supposed to work

A django app is created where all models inherits the ChainedModel model from djangochain.models

djangochain.models contains three models, Chain, Block and Operation.

The Chain model represents a certain 'blockchain' group tied to a particular django app.

The Block model represents an individual block in the Chain Model.

The Operation model represents a a database operation (which represents the 'transactions').

Each CUD operation (Create, Update, Delete) is captured by the djangochain app the on_saved and on_delete signals and traces these in a table/model called djangochain.models.Operation which are added in that table. These records has an attribute block_id consisting of an uui4 of a block it should be included in. When inserting, it is left NULL and json representations of the filter and values for the operation (DELETE, UPDATE, INSERT etc.)

When mining a new block, the system creates a new empty block, finds all saved rows of Operation model which not yet have a block_id value assigned ('unrecorded operations'), and assign that blocks to it and records a json reprsentation of the Operation in the block, and a hash computation of all that data will be the block's hash which is the base hash for the next block.

# License

MIT