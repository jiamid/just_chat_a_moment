// This is a generated file - do not edit.
//
// Generated from lib/proto/chat.proto.

// @dart = 3.3

// ignore_for_file: annotate_overrides, camel_case_types, comment_references
// ignore_for_file: constant_identifier_names
// ignore_for_file: curly_braces_in_flow_control_structures
// ignore_for_file: deprecated_member_use_from_same_package, library_prefixes
// ignore_for_file: non_constant_identifier_names, unused_import

import 'dart:convert' as $convert;
import 'dart:core' as $core;
import 'dart:typed_data' as $typed_data;

@$core.Deprecated('Use messageTypeDescriptor instead')
const MessageType$json = {
  '1': 'MessageType',
  '2': [
    {'1': 'UNKNOWN', '2': 0},
    {'1': 'SYSTEM', '2': 1},
    {'1': 'USER_TEXT', '2': 2},
    {'1': 'QUERY_COUNT', '2': 3},
    {'1': 'ROOM_COUNT', '2': 4},
    {'1': 'MUSIC', '2': 5},
  ],
};

/// Descriptor for `MessageType`. Decode as a `google.protobuf.EnumDescriptorProto`.
final $typed_data.Uint8List messageTypeDescriptor = $convert.base64Decode(
    'CgtNZXNzYWdlVHlwZRILCgdVTktOT1dOEAASCgoGU1lTVEVNEAESDQoJVVNFUl9URVhUEAISDw'
    'oLUVVFUllfQ09VTlQQAxIOCgpST09NX0NPVU5UEAQSCQoFTVVTSUMQBQ==');

@$core.Deprecated('Use chatMessageDescriptor instead')
const ChatMessage$json = {
  '1': 'ChatMessage',
  '2': [
    {'1': 'user', '3': 1, '4': 1, '5': 9, '10': 'user'},
    {'1': 'room_id', '3': 2, '4': 1, '5': 5, '10': 'roomId'},
    {'1': 'content', '3': 3, '4': 1, '5': 9, '10': 'content'},
    {'1': 'timestamp', '3': 4, '4': 1, '5': 3, '10': 'timestamp'},
    {
      '1': 'type',
      '3': 5,
      '4': 1,
      '5': 14,
      '6': '.chat.MessageType',
      '10': 'type'
    },
  ],
};

/// Descriptor for `ChatMessage`. Decode as a `google.protobuf.DescriptorProto`.
final $typed_data.Uint8List chatMessageDescriptor = $convert.base64Decode(
    'CgtDaGF0TWVzc2FnZRISCgR1c2VyGAEgASgJUgR1c2VyEhcKB3Jvb21faWQYAiABKAVSBnJvb2'
    '1JZBIYCgdjb250ZW50GAMgASgJUgdjb250ZW50EhwKCXRpbWVzdGFtcBgEIAEoA1IJdGltZXN0'
    'YW1wEiUKBHR5cGUYBSABKA4yES5jaGF0Lk1lc3NhZ2VUeXBlUgR0eXBl');
