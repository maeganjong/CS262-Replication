# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: new_route_guide.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x15new_route_guide.proto\x12\nrouteguide\"\x14\n\x04Text\x12\x0c\n\x04text\x18\x01 \x01(\t\":\n\x04Note\x12\x0e\n\x06sender\x18\x01 \x01(\t\x12\x11\n\trecipient\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x04 \x01(\t\"\x07\n\x05\x45mpty2\x83\x04\n\x04\x43hat\x12\x32\n\nlogin_user\x12\x10.routeguide.Text\x1a\x10.routeguide.Text\"\x00\x12\x35\n\rregister_user\x12\x10.routeguide.Text\x1a\x10.routeguide.Text\"\x00\x12:\n\x10\x64isplay_accounts\x12\x10.routeguide.Text\x1a\x10.routeguide.Text\"\x00\x30\x01\x12\x39\n\x11\x63heck_user_exists\x12\x10.routeguide.Text\x1a\x10.routeguide.Text\"\x00\x12\x36\n\x0e\x64\x65lete_account\x12\x10.routeguide.Text\x1a\x10.routeguide.Text\"\x00\x12.\n\x06logout\x12\x10.routeguide.Text\x1a\x10.routeguide.Text\"\x00\x12@\n\x16\x63lient_receive_message\x12\x10.routeguide.Text\x1a\x10.routeguide.Note\"\x00\x30\x01\x12;\n\x13\x63lient_send_message\x12\x10.routeguide.Note\x1a\x10.routeguide.Text\"\x00\x12\x32\n\nalive_ping\x12\x10.routeguide.Text\x1a\x10.routeguide.Text\"\x00\x42\x36\n\x1bio.grpc.examples.routeguideB\x0fRouteGuideProtoP\x01\xa2\x02\x03RTGb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'new_route_guide_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\n\033io.grpc.examples.routeguideB\017RouteGuideProtoP\001\242\002\003RTG'
  _TEXT._serialized_start=37
  _TEXT._serialized_end=57
  _NOTE._serialized_start=59
  _NOTE._serialized_end=117
  _EMPTY._serialized_start=119
  _EMPTY._serialized_end=126
  _CHAT._serialized_start=129
  _CHAT._serialized_end=644
# @@protoc_insertion_point(module_scope)
