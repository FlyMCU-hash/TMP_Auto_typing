import 'package:flutter_test/flutter_test.dart';
import 'package:peak_afk/afk_controller.dart';

void main() {
  test('间隔只接受整数', () {
    expect(parseInterval('30'), 30);
    expect(parseInterval(' 5 '), 5);
    expect(parseInterval(''), isNull);
    expect(parseInterval('abc'), isNull);
  });
}
