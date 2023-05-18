# blender-code-samples
過去にBlenderの付属のPythonのみを使用した課題にて作成したプログラムです

## 環境

- Windows 10

- Blender : 3.2.2

## 使用方法
1. Blenderを起動しScriptingタブからファイルを開いて.pyを読み込む
2. スクリプト実行をし待機する(本プログラムはオブジェクトを大量に生成するため長時間[1]の待機が必要です)
3. 画像や動画化する場合はレンダリングを行ってください。[レンダリングについてその他参照](#その他)
4. VRの動画としてみるには[Spatial Media Metadata Injector](https://github.com/google/spatial-media)などを使用し変換してください

## プログラムについて
- プログラム実行時にデスクトップに恒星データなどを格納するための一時フォルダを生成します。
- 恒星データは[ヒッパルコス星表](http://astro.starfree.jp/commons/hip/)のデータを使用し主要な恒星がまとめられた[データ](http://astro.starfree.jp/commons/hip/hip_lite_major.csv)を用いています。データサイズは3215個あるためBlenderでの生成にはとても時間がかかります。


## その他
- 解像度の変更<br>
ソースコードの解像度の設定をいじることで変更することもできます。
- レンダリングについて<br>
4Kの解像度のレンダリングには[Google Colaboratory](https://colab.research.google.com/)の無料枠を使用して**1フレーム約2分**程度かかったためリソースのあるPC以外ではColabを使用することをおすすめします。使用したノートは[こちら](https://colab.research.google.com/github/ynshung/blender-colab/blob/master/blender_render.ipynb)です<br>
**現在設定されているレンダリングの時間が48フレームあり数時間レンダリングにかかるため適宜に調整してください。**
- Google Colabを使用する場合の注意点<br>
Blender(version 3.2.2時点)では日本語テキストの表示は用意されているフォントで描画ができません。星座の名前を日本語対応させるためにプログラムでWindows標準のフォントを読み込んでいます。<br>
本題のGoogle Colabを使用する場合は**パック化**させてください。手順は以下の通りです。<br>
  > ファイル → 外部データ → リソースをパック

[1]intel core i7を積んだノートパソコンで約10分

# License
This software is released under the MIT License, see LICENSE.