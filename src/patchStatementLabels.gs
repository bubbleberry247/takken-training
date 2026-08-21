// patchStatementLabels.gs
//
// 公式原典照合で confirmed_missing となった宅建士51問の、stem内ラベルだけを
// 安全に局所更新する管理者専用メンテナンス関数。
//
// - R6takken-028（blocked）とR3問38の2件は固定allowlistから除外する。
// - 公開RPC/UIから呼び出さない。引数なしwrapperはdry-run専用入口。
// - QuestionBankの書込みはstem列限定のAdvanced Sheets API batchUpdateのみ。
// - 全量import、シートclear、SpreadsheetAppによるQuestionBank逐次書込みは行わない。
// - 公式原典URL・PDF SHA-256・ページは固定ledger証跡としてspecに埋め込むが、
//   Loggerには本文・URLを出さない。

var TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_SHEET_ = '_QuestionBankStatementLabelPatchBackup';
var TAKKEN_STATEMENT_LABEL_PATCH_MAINTENANCE_PROPERTY_ = 'TAKKEN_STATEMENT_LABEL_PATCH_MAINTENANCE_WINDOW';
var TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_ = 51;
var TAKKEN_STATEMENT_LABEL_PATCH_NON_TARGET_COUNT_ = 549;
var TAKKEN_STATEMENT_LABEL_PATCH_BLOCKED_QIDS_ = {
  'R6takken-028': true,
  'R3atakken-038': true,
  'R3btakken-038': true
};

var TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_ = [
  'patchId', 'createdAt', 'patchStatus', 'dbSpreadsheetId', 'targetQId', 'sourceRowNumber',
  'afterSourceRowNumber', 'beforeRowSha256', 'afterRowSha256',
  'beforeInventorySha256', 'beforeNonTargetInventorySha256', 'beforeInventoryOrderSha256',
  'afterInventorySha256', 'afterNonTargetInventorySha256', 'afterInventoryOrderSha256',
  'qId', 'segmentId', 'type', 'difficulty',
  'tag1', 'tag2', 'tag3', 'lawTag',
  'revisionFlag', 'conceptId', 'variantGroupId', 'source_ref',
  'imageUrl', 'choiceImageUrl',
  'stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
  'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
  'correct', 'explainShort', 'explainLong', 'status', 'updatedAt'
];

// GENERATED FROM data/statement_label_corrections.csv.
// Each spec contains hashes/offsets/official-source metadata only; it does
// not contain the long question body.
var TAKKEN_STATEMENT_LABEL_PATCH_SPECS_ = [
  {
    "qId": "H28takken-007",
    "expectedBeforeStemSha256": "7871e3748f80a15fc2f83bdc8260cdb51ee3d5f617899d7012da54d76bdd328b",
    "replacementStemSha256": "d816d218d6a4360c0681b8f01afaa562222d3643111393a09c62f80a738f8591",
    "expectedLabelSequence": "ア・イ・ウ",
    "insertionOffsets": [
      137,
      187,
      243
    ],
    "sourceStatementCount": 3,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H28-q_a.pdf",
    "officialPdfSha256": "87923a2870184f9a0a26c76c056255aa94fa50242ff9aeda0a61eadf64699983",
    "pdfPage": 5,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2016/07.html",
    "sourceHash": "cbf4ee8281d480fef7476db7f140813d08334dc3c80d760c586d6412dc23ff43"
  },
  {
    "qId": "H28takken-028",
    "expectedBeforeStemSha256": "e4c9bb4090e7b390a771c9de8bcc4b0f0cf6b17d2918eedbdfa1c478e72bd0f8",
    "replacementStemSha256": "33d6f55c6d9bb8a802a0ae53a7523f083c2aa6d21a3cd7e85dc2926cf365f7b2",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      120,
      223,
      292,
      372
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H28-q_a.pdf",
    "officialPdfSha256": "87923a2870184f9a0a26c76c056255aa94fa50242ff9aeda0a61eadf64699983",
    "pdfPage": 15,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2016/28.html",
    "sourceHash": "16af863bb3c2151fb094de6f1b1e9692de11f7436aa213c3aa831c7a4b68b244"
  },
  {
    "qId": "H28takken-029",
    "expectedBeforeStemSha256": "e73650739c7fcbae8e511718db9ea43a681161deec5adb8f1e61e103b1ed51b2",
    "replacementStemSha256": "8bbdf421d51f916ef1f1f8f3046ea9a703352f4fe40d52e0ea07556c44ebeae7",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      69,
      164,
      222,
      298
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H28-q_a.pdf",
    "officialPdfSha256": "87923a2870184f9a0a26c76c056255aa94fa50242ff9aeda0a61eadf64699983",
    "pdfPage": 15,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2016/29.html",
    "sourceHash": "7f252d00393edd44d4ea7e0ca17c4c673f0164ac512a981ce048fbbee4c19580"
  },
  {
    "qId": "H28takken-033",
    "expectedBeforeStemSha256": "4a1831b2004ab73190250f4fda15b17fd1417a496dc9d77324979ba291dd9b44",
    "replacementStemSha256": "e5957b8103d4b6b875c418f98642130974e0fc8338747e7fc73072d9421d5c46",
    "expectedLabelSequence": "ア・イ・ウ",
    "insertionOffsets": [
      74,
      162,
      237
    ],
    "sourceStatementCount": 3,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H28-q_a.pdf",
    "officialPdfSha256": "87923a2870184f9a0a26c76c056255aa94fa50242ff9aeda0a61eadf64699983",
    "pdfPage": 17,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2016/33.html",
    "sourceHash": "fe506c23d5ef121270902a1b351b0d1f1b72180da84fd96d7a50bb08d34bd021"
  },
  {
    "qId": "H28takken-036",
    "expectedBeforeStemSha256": "3c8219eafacd07cf8605d8d7d7b2487987099eef5086cb5ba88b9e9781b13263",
    "replacementStemSha256": "0cdb7a91ea559e60538322812a4fa19e056d8fd0d53ee8dd02e7f53290d500d9",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      60,
      181,
      272,
      376
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H28-q_a.pdf",
    "officialPdfSha256": "87923a2870184f9a0a26c76c056255aa94fa50242ff9aeda0a61eadf64699983",
    "pdfPage": 19,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2016/36.html",
    "sourceHash": "adab5fa4cf746f1a2519e6f9720ab2f11b3c19a5935dc40f469058e4a5835de1"
  },
  {
    "qId": "H28takken-037",
    "expectedBeforeStemSha256": "c980aa2ee08aff03442312953f9f47e7d4fa1e402fe1f062e306646dfac0f0eb",
    "replacementStemSha256": "08f700d1d31e4464e100a0b22abac7848ba27e8e868d5c8f6636abedcd119d39",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      54,
      156,
      275,
      359
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H28-q_a.pdf",
    "officialPdfSha256": "87923a2870184f9a0a26c76c056255aa94fa50242ff9aeda0a61eadf64699983",
    "pdfPage": 20,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2016/37.html",
    "sourceHash": "cfaa6dd51474c7355f627b377ce90906973c11a6e2a0e3f5a2a72fecf9cfd0fd"
  },
  {
    "qId": "H28takken-038",
    "expectedBeforeStemSha256": "8b7349f7e51b2505b515601b2362c593023b3a6560784c8bd725e33fc39fee65",
    "replacementStemSha256": "b55c9d2f4f69f5fe303801deb6c185d50636355d4cd02def38066e23c41e6f8b",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      80,
      178,
      303,
      432
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H28-q_a.pdf",
    "officialPdfSha256": "87923a2870184f9a0a26c76c056255aa94fa50242ff9aeda0a61eadf64699983",
    "pdfPage": 21,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2016/38.html",
    "sourceHash": "c39ad18f731554c5866a28c144b5e7c038143c0bea68cbed469c264e28ea4165"
  },
  {
    "qId": "H28takken-043",
    "expectedBeforeStemSha256": "a8d10debb3c3e1c02ffe9c8f0ff2dcf43f35fbacb7d15caf0826547a8b94c56d",
    "replacementStemSha256": "991744b07400d9cf4be23846de75f0a2f402e7367970af6e9b892e9fc7df1668",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      143,
      213,
      323,
      421
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H28-q_a.pdf",
    "officialPdfSha256": "87923a2870184f9a0a26c76c056255aa94fa50242ff9aeda0a61eadf64699983",
    "pdfPage": 23,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2016/43.html",
    "sourceHash": "41248347ac2d79c9f12bdf9d8d717d2b8b833dc8aee1ab382da4502f23402863"
  },
  {
    "qId": "H29takken-016",
    "expectedBeforeStemSha256": "64827ccb4aea1a03500b624e98c4a540a24b25f0626fb8a93fe37d2b5059d1ca",
    "replacementStemSha256": "82d3e9b8ba1bbae173aef6f59caefeabf9372761a80d955e5249c45b707987fb",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      31,
      123,
      205,
      319
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H29-q_a.pdf",
    "officialPdfSha256": "8dea64d2b2eef90b99fc5c2e00c1bab86ec59aa16a8619d179df20ca215f162c",
    "pdfPage": 9,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2017/16.html",
    "sourceHash": "c73eb39501a5392e5b21c1298c431603a3274ef54647fba94e840a560b7b43e2"
  },
  {
    "qId": "H29takken-027",
    "expectedBeforeStemSha256": "2fb5e7025e7527d4ff08317d101b7ab0b9ddeca8c9904ebbe931b25b1c339beb",
    "replacementStemSha256": "06e567f9fb87ad0103209340b5975f65b751c2b0ec9400036b58580c0997000d",
    "expectedLabelSequence": "ア・イ・ウ",
    "insertionOffsets": [
      92,
      203,
      301
    ],
    "sourceStatementCount": 3,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H29-q_a.pdf",
    "officialPdfSha256": "8dea64d2b2eef90b99fc5c2e00c1bab86ec59aa16a8619d179df20ca215f162c",
    "pdfPage": 14,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2017/27.html",
    "sourceHash": "b5efc5b65cb8f82522e4605e3da3668867135fadd360e539a7b0d606854ce889"
  },
  {
    "qId": "H29takken-028",
    "expectedBeforeStemSha256": "8d059d0ec1638af2500dbbc4ee25b697bc95bb2d4143dc5b35905d65653ab7f4",
    "replacementStemSha256": "63b9bb5b54ea7116633b40ee9e712392d85e2584b7528228873bcd004ffabd44",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      71,
      147,
      227,
      337
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H29-q_a.pdf",
    "officialPdfSha256": "8dea64d2b2eef90b99fc5c2e00c1bab86ec59aa16a8619d179df20ca215f162c",
    "pdfPage": 15,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2017/28.html",
    "sourceHash": "65c1745ea15ccda5fe7ae331de70a13fcd44c53899c4987ce0f628ed6ff6da08"
  },
  {
    "qId": "H29takken-031",
    "expectedBeforeStemSha256": "9e47a768a3e1e0d461541eeba1c8bd15bf6bc2b449279236b1fbd25a7ac4d172",
    "replacementStemSha256": "b812bcfcb11055d4ddc44ba4cafae7717ffea765bde925eaba7fb9617b8712a5",
    "expectedLabelSequence": "ア・イ・ウ",
    "insertionOffsets": [
      126,
      204,
      277
    ],
    "sourceStatementCount": 3,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H29-q_a.pdf",
    "officialPdfSha256": "8dea64d2b2eef90b99fc5c2e00c1bab86ec59aa16a8619d179df20ca215f162c",
    "pdfPage": 16,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2017/31.html",
    "sourceHash": "f09e9797ad7f8d57081137789992ceb61bb28449ab1a141646c18bac454d73e1"
  },
  {
    "qId": "H29takken-039",
    "expectedBeforeStemSha256": "13fbd633efe50916bad64b4e4635cfa5290149d2e5892b5167158f308cdac747",
    "replacementStemSha256": "9395d3632e08f1e66b01da2700a1cf92ecb0d98e568cbace3d50fb910665e1e6",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      110,
      197,
      310,
      367
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H29-q_a.pdf",
    "officialPdfSha256": "8dea64d2b2eef90b99fc5c2e00c1bab86ec59aa16a8619d179df20ca215f162c",
    "pdfPage": 20,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2017/39.html",
    "sourceHash": "599dedc1c48005757cb3d1b1161e0b93f20fba70022a65784427c3b17cc328d2"
  },
  {
    "qId": "H29takken-042",
    "expectedBeforeStemSha256": "2da5e391f645fb4287909d821f8bad96dbd4fefce146ff42408cce54a00d418a",
    "replacementStemSha256": "486ca36f8669d1f7301c7223b54511cf7f319fdcad6dfb6112e42980cf2d6e89",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      54,
      100,
      199,
      297
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H29-q_a.pdf",
    "officialPdfSha256": "8dea64d2b2eef90b99fc5c2e00c1bab86ec59aa16a8619d179df20ca215f162c",
    "pdfPage": 22,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2017/42.html",
    "sourceHash": "7f83a84168cb51f70e5796d8882491a747b99f89e958cb02a51f84230ee0c2f6"
  },
  {
    "qId": "H29takken-043",
    "expectedBeforeStemSha256": "562184444c1af5d29d594f192a9cf64c5da65a4f3047873b3c026cd3c76f697a",
    "replacementStemSha256": "9b8fb4540e2d285757d80c16306d3e7dbddc4036c1ebade027c47ee61f3d3c36",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      127,
      228,
      341,
      447
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H29-q_a.pdf",
    "officialPdfSha256": "8dea64d2b2eef90b99fc5c2e00c1bab86ec59aa16a8619d179df20ca215f162c",
    "pdfPage": 23,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2017/43.html",
    "sourceHash": "42888f38139ed1cc8d1239f5a0fb5207f3e144717aaf11fc69d502d69a802d15"
  },
  {
    "qId": "H30takken-028",
    "expectedBeforeStemSha256": "e7d0eb37a8fe7e0d9aaa599176fbe1d7f246adfcbf19fda32e9c2c27e85540a9",
    "replacementStemSha256": "50af6c8c940e53c474773ae55282fa06b17df3214436581fe84ada8bacbadb30",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      55,
      156,
      227,
      329
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H30-q_a.pdf",
    "officialPdfSha256": "f2fb8a79c7c6394b6a397383df5551b898e03aa684d162073b291a22fbe3ed72",
    "pdfPage": 15,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2018/28.html",
    "sourceHash": "7cbcedcaef6452f8d31cc7f8c0a449702f702af0f2ba61979f25cc2a5b335e00"
  },
  {
    "qId": "H30takken-034",
    "expectedBeforeStemSha256": "358f950abedac1e7e886e85da64758aaf1f7d6b58d45e80cda63abcad3e0c0d3",
    "replacementStemSha256": "d83e3642ad228f61816cf751897fb23279cfba755c5a645968b4fa7c7914c8ed",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      98,
      144,
      168,
      177
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H30-q_a.pdf",
    "officialPdfSha256": "f2fb8a79c7c6394b6a397383df5551b898e03aa684d162073b291a22fbe3ed72",
    "pdfPage": 18,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2018/34.html",
    "sourceHash": "348a0ea8f78745ee04feb7a6a6c366d443d592c4746db83407fcf3de1b6c333e"
  },
  {
    "qId": "H30takken-037",
    "expectedBeforeStemSha256": "5ef67be1d402e1565ab2b041e3262455ca4927b16c3ae4d78ab31fa9a6c680e0",
    "replacementStemSha256": "4ad8aa35d3193eef4f4b53eaaf9e15c25c8adf9772f136d3978557cb0ad21b38",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      129,
      237,
      309,
      406
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H30-q_a.pdf",
    "officialPdfSha256": "f2fb8a79c7c6394b6a397383df5551b898e03aa684d162073b291a22fbe3ed72",
    "pdfPage": 20,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2018/37.html",
    "sourceHash": "b386ea3554161d02415b5f7909f11f5b171bfd394d7d3d39009755353e468bdd"
  },
  {
    "qId": "H30takken-040",
    "expectedBeforeStemSha256": "d373cc81141c0caf3fa5149baf768f649c1f326091bb6aaaf3a0ee8730630e42",
    "replacementStemSha256": "1a40826d86191b9a08e2d05d9b25f0301fce4bb43f491f4143e9c9e1736b0870",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      52,
      122,
      198,
      276
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/H30-q_a.pdf",
    "officialPdfSha256": "f2fb8a79c7c6394b6a397383df5551b898e03aa684d162073b291a22fbe3ed72",
    "pdfPage": 22,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2018/40.html",
    "sourceHash": "ab844c92dce46a12a8494671f92e15b2a91c54b02b4b28e3404d9d5cbb8b2a99"
  },
  {
    "qId": "R1takken-027",
    "expectedBeforeStemSha256": "e0b9571005e0178f506628a44ae94093e2f97f7eae88440028023d6a5dfaca46",
    "replacementStemSha256": "167d538dbc366c0a425b44415b3ece583b67a9785351ff399398e434a7300620",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      61,
      134,
      291,
      348
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R1-q_a.pdf",
    "officialPdfSha256": "c0fe7658da533768c01904ce1aa298b204f6c6309cee6c475ff5e3d46a97b772",
    "pdfPage": 14,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2019/27.html",
    "sourceHash": "02e6389cae8d5dffff9fa19a34e9a9b14a31f16e73d6061f4399019c1e49c295"
  },
  {
    "qId": "R1takken-029",
    "expectedBeforeStemSha256": "233398c6b284ede4919ba8d694b507f8d70f4e9e352b1b42700f4385f096377f",
    "replacementStemSha256": "e5e6e2412913152f5b6cb1204d411d301b1edb6aa3f24f3416beb67335d2c71b",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      66,
      180,
      264,
      329
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R1-q_a.pdf",
    "officialPdfSha256": "c0fe7658da533768c01904ce1aa298b204f6c6309cee6c475ff5e3d46a97b772",
    "pdfPage": 15,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2019/29.html",
    "sourceHash": "eb0574fa7cec204984382986945377dcff2d6f145087937ae898e28c5ad9e8ff"
  },
  {
    "qId": "R1takken-030",
    "expectedBeforeStemSha256": "af090594b41d8d96168ebcab94062a0987cb51a2ac4839aa0f2efd922ae7456f",
    "replacementStemSha256": "b8fcce9845ad3946952bf91ac604c4266b1c9a6496941c40d86602faa14062fb",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      51,
      138,
      191,
      267
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R1-q_a.pdf",
    "officialPdfSha256": "c0fe7658da533768c01904ce1aa298b204f6c6309cee6c475ff5e3d46a97b772",
    "pdfPage": 16,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2019/30.html",
    "sourceHash": "0d1e972086d296eb5b960b508ba85c5779cd6a97af895eceee02c1490c52955e"
  },
  {
    "qId": "R1takken-031",
    "expectedBeforeStemSha256": "e0502fa859790537684b951b65a36cfe0c5cf33264dda0a357eafe601584998f",
    "replacementStemSha256": "e8f882cc6e3e29c96bf986a678131aa639622dcf286fe02439e546842c2a39b3",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      119,
      196,
      240,
      289
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R1-q_a.pdf",
    "officialPdfSha256": "c0fe7658da533768c01904ce1aa298b204f6c6309cee6c475ff5e3d46a97b772",
    "pdfPage": 16,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2019/31.html",
    "sourceHash": "da50ba0dcede1315f16155341b63c7691ee772d995b1727bec89b8e20b28e84d"
  },
  {
    "qId": "R1takken-036",
    "expectedBeforeStemSha256": "38a9232b15ed31064660b5ed5666b2d03e8d7a48d5da011b5c8117ff6edba2fd",
    "replacementStemSha256": "00452d92bab30648cea1574f72d6cfeb997fd07d595747c75cdfc7eb2ee1ebd9",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      154,
      257,
      368,
      478
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R1-q_a.pdf",
    "officialPdfSha256": "c0fe7658da533768c01904ce1aa298b204f6c6309cee6c475ff5e3d46a97b772",
    "pdfPage": 19,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2019/36.html",
    "sourceHash": "ece9db3ae28d9fded8f7fb98b4ba4477cd98746415f741c662e3c2376c523235"
  },
  {
    "qId": "R1takken-038",
    "expectedBeforeStemSha256": "7e757da6df93dbc834d3ab69dc2e7d9abe1db2180a65f860de25bc365359db80",
    "replacementStemSha256": "9e341571fba3889b974a17d3e49cd5b00ae775ce375d31dab53fd4a40054223b",
    "expectedLabelSequence": "ア・イ・ウ",
    "insertionOffsets": [
      115,
      192,
      357
    ],
    "sourceStatementCount": 3,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R1-q_a.pdf",
    "officialPdfSha256": "c0fe7658da533768c01904ce1aa298b204f6c6309cee6c475ff5e3d46a97b772",
    "pdfPage": 20,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2019/38.html",
    "sourceHash": "21c5cc436201b6d995d28181d231282108f2d59d0de47ad50313a7a344b08b14"
  },
  {
    "qId": "R2atakken-027",
    "expectedBeforeStemSha256": "ddfaffc0b16042e3248cd010646bbfe208b1f2d39d2611bda786b5b3f3380b04",
    "replacementStemSha256": "2ab13de84698774914006eb87694d4c59b010ea51aa67cf9d2ed077401f56b51",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      62,
      195,
      314,
      371
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question.pdf",
    "officialPdfSha256": "a6dd351660b249a88c9d641bc3f82f2e13c06f9edc429b50b179c90efac61af4",
    "pdfPage": 16,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-1/27.html",
    "sourceHash": "5d24a253b720466007f70450c941906faa6a81e021043a962f262e5bcd25da25"
  },
  {
    "qId": "R2atakken-029",
    "expectedBeforeStemSha256": "39f5b20572d9e483f32cbf2fb7e891878107c2e53540cc20921a64e8ccfdd42d",
    "replacementStemSha256": "2bff07388db00405b253777e3df83e9b6d88f2b16c4b4973f5ed0c8ccc60bf60",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      142,
      212,
      309,
      391
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question.pdf",
    "officialPdfSha256": "a6dd351660b249a88c9d641bc3f82f2e13c06f9edc429b50b179c90efac61af4",
    "pdfPage": 17,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-1/29.html",
    "sourceHash": "4b99c3d82975db4b7c0c123037e7d533e2273dc1faf6ffdb223298f2a531180e"
  },
  {
    "qId": "R2atakken-037",
    "expectedBeforeStemSha256": "1f7da34c20a816fa087da95af3d2b2a202141bf8d573aade93d3bd433fd9f0ff",
    "replacementStemSha256": "d83af2d73f5133456e956bf4a4c213ff2e7cf901ab96bc8bccf9423dac8837cf",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      163,
      210,
      242,
      284
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question.pdf",
    "officialPdfSha256": "a6dd351660b249a88c9d641bc3f82f2e13c06f9edc429b50b179c90efac61af4",
    "pdfPage": 21,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-1/37.html",
    "sourceHash": "29cca6dc028c3688501ef1171e510bbb89608f97982fa548f352c054df69a1d9"
  },
  {
    "qId": "R2atakken-040",
    "expectedBeforeStemSha256": "cfda401dbe385367fa13877398c0b2ae3d9473ac9995d243a4aea933ab44d4b7",
    "replacementStemSha256": "5b69ceb0364f3e66ee7dfc98a6392db6923e51049ed2b344697df3488570e513",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      137,
      242,
      309,
      373
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question.pdf",
    "officialPdfSha256": "a6dd351660b249a88c9d641bc3f82f2e13c06f9edc429b50b179c90efac61af4",
    "pdfPage": 23,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-1/40.html",
    "sourceHash": "c9a708f62e7445c1dbd1bf72bf58b2ba48684156195f182c04a29eac33788579"
  },
  {
    "qId": "R2btakken-008",
    "expectedBeforeStemSha256": "c2108a15d32450ab23f78f8565608d9d70b36b717a38b47f164219b6532b65e4",
    "replacementStemSha256": "713704458d0cdba16e75b1f2e5f7cc81b1bc032eb3aa5673df777e92b8ecf87c",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      69,
      121,
      188,
      243
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question_002.pdf",
    "officialPdfSha256": "3e771375cee071c58baf64f51d5ca344163a45f1df00ef18abf2402c7bf24104",
    "pdfPage": 5,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-2/08.html",
    "sourceHash": "05d7c5d2ee2c22bb5b1d34620d2bcf3b359ae634f315015e7720418b13f7316c"
  },
  {
    "qId": "R2btakken-028",
    "expectedBeforeStemSha256": "fa3d282302ed8d35898d6c6076ef838313c96ff140e618ed17a18aa71732593e",
    "replacementStemSha256": "f98ff9f48ceacb5dc3c331a30256735f94c5e9502c0e90f6712615ebfc37ad1a",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      168,
      287,
      351,
      525
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question_002.pdf",
    "officialPdfSha256": "3e771375cee071c58baf64f51d5ca344163a45f1df00ef18abf2402c7bf24104",
    "pdfPage": 15,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-2/28.html",
    "sourceHash": "a0294609b13c16b7f07fec623430dbdfe5ea85afe73fdfb76e05036ac81a6acd"
  },
  {
    "qId": "R2btakken-032",
    "expectedBeforeStemSha256": "08ed02b180133929c13a7a36a7b3b154b8029d9bc8b17ffe7b84588b010e6056",
    "replacementStemSha256": "03e2448e1040ec06807526c38eceb0a75a97cf410f87355eb7d03dad375b9325",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      88,
      189,
      284,
      356
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question_002.pdf",
    "officialPdfSha256": "3e771375cee071c58baf64f51d5ca344163a45f1df00ef18abf2402c7bf24104",
    "pdfPage": 17,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-2/32.html",
    "sourceHash": "2934e9d42b23e46b1544642fc91f3e05e8a5eb63e7bf9260bd112691fe7b96c9"
  },
  {
    "qId": "R2btakken-035",
    "expectedBeforeStemSha256": "028c53d96d550fc6396c8ca84981997eec7d36d28aae5c54d6f0b02daf2f7a8b",
    "replacementStemSha256": "7c595e4a572ef80089d5456e377aa39fa27e69c1b49e592f3ee2827b1fef01e6",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      146,
      230,
      317,
      414
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question_002.pdf",
    "officialPdfSha256": "3e771375cee071c58baf64f51d5ca344163a45f1df00ef18abf2402c7bf24104",
    "pdfPage": 19,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-2/35.html",
    "sourceHash": "264f21fe3ac8d8b5107fb2e77217a6045b516b32f03e4fbeeb9f2bb9f72d2ae7"
  },
  {
    "qId": "R2btakken-038",
    "expectedBeforeStemSha256": "1caaba71e5a2c7320b0b6ce07960ea7a05845d5f45ffc49e0803d76a1f147346",
    "replacementStemSha256": "bfc8b5b38597436a1f42b1664134fdd15e92feda719c182c71ef52ba9e48e131",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      52,
      169,
      225,
      314
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question_002.pdf",
    "officialPdfSha256": "3e771375cee071c58baf64f51d5ca344163a45f1df00ef18abf2402c7bf24104",
    "pdfPage": 20,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-2/38.html",
    "sourceHash": "ff3908b72e39b4e0758e79503a3361c511c209d8d3bee4fc29c9b9a582cb7e23"
  },
  {
    "qId": "R2btakken-044",
    "expectedBeforeStemSha256": "401508a4a5568cae2f16f4a4f559dd4d9834a2bf6f4f8b65a63ed3f8e37d51df",
    "replacementStemSha256": "d9e36638a1f4ccb3055e4b6c834873cb2e0a0c5bdcae16111f8dd980a728aca3",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      33,
      92,
      133,
      186
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R2-question_002.pdf",
    "officialPdfSha256": "3e771375cee071c58baf64f51d5ca344163a45f1df00ef18abf2402c7bf24104",
    "pdfPage": 24,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2020-2/44.html",
    "sourceHash": "856a10edc0f60db63a0b713c2365e33b8dd0363f95a1665b7086fbf251403f29"
  },
  {
    "qId": "R3atakken-003",
    "expectedBeforeStemSha256": "5607a695c548ca8ea74bbc0b007dbd2c2a621edbbe476b3c3572cb4c777b1d71",
    "replacementStemSha256": "31644a2155850682a392bfe0afd5f71430b0dec8e6f7f4ba2d59da64fa62ce56",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      87,
      169,
      286,
      366
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question.pdf",
    "officialPdfSha256": "ad436ace2388e21860ea59b7bbd9482a0b4d15422737f3fc1b44291764569219",
    "pdfPage": 4,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-1/03.html",
    "sourceHash": "35ed72c364d987fec5795b05631d48a0550dce9522ab7191c079e376450181c8"
  },
  {
    "qId": "R3atakken-030",
    "expectedBeforeStemSha256": "d8ab9460b290e56b292c37ddadbb87c791c29b4dd63b61a4fe6d4076c7cb8429",
    "replacementStemSha256": "d0fb01339223ecfdec9f57841de4a8620083c055d1ea1974306586e8633ef556",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      62,
      114,
      189,
      259
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question.pdf",
    "officialPdfSha256": "ad436ace2388e21860ea59b7bbd9482a0b4d15422737f3fc1b44291764569219",
    "pdfPage": 18,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-1/30.html",
    "sourceHash": "a303f27fecce1666e452c1f7616199314c6ec8980bf2e94ab60084a717581952"
  },
  {
    "qId": "R3atakken-035",
    "expectedBeforeStemSha256": "fcf5e5e152efc308d34a74b5d96df67a814e1d2dd53f8dd971a35e8a5f8988c3",
    "replacementStemSha256": "867000081212437cfd13eebd143ff7b676375c79d9d7779069df02340099f906",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      64,
      157,
      286,
      346
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question.pdf",
    "officialPdfSha256": "ad436ace2388e21860ea59b7bbd9482a0b4d15422737f3fc1b44291764569219",
    "pdfPage": 20,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-1/35.html",
    "sourceHash": "6d1b05968fbba590c850cfeb218001ebb121929ca9690b4e22371070edd7ee93"
  },
  {
    "qId": "R3atakken-041",
    "expectedBeforeStemSha256": "9a9a4152b8d2b0cd804475c4b7f522b4b965c207feac252cb71057afe6ebcfc8",
    "replacementStemSha256": "9790686dadbf9118e00cd64d4e58f880a13afde9e5ba94c030d9beef50c4da4e",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      103,
      209,
      310,
      363
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question.pdf",
    "officialPdfSha256": "ad436ace2388e21860ea59b7bbd9482a0b4d15422737f3fc1b44291764569219",
    "pdfPage": 23,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-1/41.html",
    "sourceHash": "1859e92a9001a0d6c32bbf389ce1b0a98b4ef373a98c068d6cb5445936b932f3"
  },
  {
    "qId": "R3atakken-043",
    "expectedBeforeStemSha256": "d8ae8e5ceba766a887bc2ee25265bb5280cf9ad26a1e2507a17dfdfa19862df1",
    "replacementStemSha256": "ceda0d562a26c31a5367ff2496d5794a61297e581554dc240fa0f6ea57c844d2",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      49,
      115,
      203,
      262
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question.pdf",
    "officialPdfSha256": "ad436ace2388e21860ea59b7bbd9482a0b4d15422737f3fc1b44291764569219",
    "pdfPage": 24,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-1/43.html",
    "sourceHash": "0684b6f4451178f4355effaca52b7720648ec4364f2943056c2ef59eaf038a68"
  },
  {
    "qId": "R3btakken-028",
    "expectedBeforeStemSha256": "b4e5936aa1ee0be9965357ca3d2628808e71a4c36b77f3203a862aefd0a15a04",
    "replacementStemSha256": "afca1afc7a756ed6d0874cd18ff790164942cda51fed40c73ec4f6ab4ee1a9dc",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      88,
      142,
      198,
      278
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question_002.pdf",
    "officialPdfSha256": "88beed8b5280e76b35b57c2894ed3be35453ccf3dfc76dbc2d8f6ff195b74e45",
    "pdfPage": 16,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-2/28.html",
    "sourceHash": "902e0c6c09fbb25e4447e2a39f887cd41d5f4084665867c24f169a4305fdbc1e"
  },
  {
    "qId": "R3btakken-031",
    "expectedBeforeStemSha256": "a8cbc68ef03629964306b42c1a50a7b46c3319ccd9649331285e8e14453fac03",
    "replacementStemSha256": "d0154e1c52e597783b270a30ea8ee5b84b0221759b1f7762f78c07e6961a0bc9",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      253,
      330,
      390,
      461
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question_002.pdf",
    "officialPdfSha256": "88beed8b5280e76b35b57c2894ed3be35453ccf3dfc76dbc2d8f6ff195b74e45",
    "pdfPage": 18,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-2/31.html",
    "sourceHash": "0bfbc97443a82703f75077e7e6a4d373f69b8509761b6ecce7f3689f35436322"
  },
  {
    "qId": "R3btakken-033",
    "expectedBeforeStemSha256": "a365d59264c3a4260942626dae12bc9cf916228a256c3f44582ae798be34fc1e",
    "replacementStemSha256": "6fc1fd581c1f0a4f5e8ca2d3c04920e2f3a35a5836ab1d22e5ec19c4f9a938b3",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      166,
      234,
      356,
      429
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question_002.pdf",
    "officialPdfSha256": "88beed8b5280e76b35b57c2894ed3be35453ccf3dfc76dbc2d8f6ff195b74e45",
    "pdfPage": 19,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-2/33.html",
    "sourceHash": "9da506ab64086ce1a0b36471d228af6e29185c9732890e945f427ac6da3600bb"
  },
  {
    "qId": "R3btakken-042",
    "expectedBeforeStemSha256": "3e0e0d89e911b40fe1566745a7bb1e57e179012b78518484932709f79bfb9fa1",
    "replacementStemSha256": "5a3c3698ec39d8b39a2d206ce4bb1a94d8573775ed80499d7f392e4ee6698774",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      150,
      193,
      246,
      268
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question_002.pdf",
    "officialPdfSha256": "88beed8b5280e76b35b57c2894ed3be35453ccf3dfc76dbc2d8f6ff195b74e45",
    "pdfPage": 23,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-2/42.html",
    "sourceHash": "b42cdd075cb337c86d7a3f6877e0853fd1209039d6f9f5117449b17e75bf0d0a"
  },
  {
    "qId": "R3btakken-044",
    "expectedBeforeStemSha256": "723656a82c3ccc91b7f162c5afb715b6df380017c55a7a05a78d3606d47b17e4",
    "replacementStemSha256": "f4b884e411b052d693b5319091eea44152b481489ac9b4f141beb060e741d27b",
    "expectedLabelSequence": "ア・イ・ウ",
    "insertionOffsets": [
      89,
      213,
      316
    ],
    "sourceStatementCount": 3,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/12/R3-question_002.pdf",
    "officialPdfSha256": "88beed8b5280e76b35b57c2894ed3be35453ccf3dfc76dbc2d8f6ff195b74e45",
    "pdfPage": 25,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2021-2/44.html",
    "sourceHash": "d8d0d42289a0318d0a037a97aed00b7fe54580d66baa54a1038be0f3da5b691f"
  },
  {
    "qId": "R4takken-009",
    "expectedBeforeStemSha256": "4cbfaecac00466ac0f0722448a1709f454da5930dbc7f56bb386629dd3ccb8bd",
    "replacementStemSha256": "07d457a3c5fd239ceb69b59dced8219ae09c61efbab3cb656292df4cf758f5a1",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      37,
      113,
      162,
      206
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R4-q_a.pdf",
    "officialPdfSha256": "44baadbfaf0c5b3a872f107a4bc476d9c5a6516b3a6a0ca68678220c2271cf50",
    "pdfPage": 7,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2022/09.html",
    "sourceHash": "6e5f30ef1062fe520d37827e31269d501df3738b7bbf722738c8fd550abc24d3"
  },
  {
    "qId": "R4takken-030",
    "expectedBeforeStemSha256": "5d868d677b2a65ea4f676057496746111f71ed56cdad39987169ed4ecfd195a6",
    "replacementStemSha256": "9549225783c5db4f44f89cf84d3d2c2d2420be9dac7aafb63ba1492eb26182e0",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      75,
      165,
      243,
      309
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R4-q_a.pdf",
    "officialPdfSha256": "44baadbfaf0c5b3a872f107a4bc476d9c5a6516b3a6a0ca68678220c2271cf50",
    "pdfPage": 17,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2022/30.html",
    "sourceHash": "08379292752679981b6718a734f9ecf3daf13604aff73fb27b52c0ecc5c92843"
  },
  {
    "qId": "R4takken-033",
    "expectedBeforeStemSha256": "dafe3c5b0c6160d578b33c7a058de0e3b6721ed3d635a863c41129baa2bc84cf",
    "replacementStemSha256": "8386e23ad44a49e10d0bb158fbbf7e4003f46e222f46a58993d0b0c120b97246",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      48,
      116,
      195,
      308
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R4-q_a.pdf",
    "officialPdfSha256": "44baadbfaf0c5b3a872f107a4bc476d9c5a6516b3a6a0ca68678220c2271cf50",
    "pdfPage": 18,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2022/33.html",
    "sourceHash": "bb602ff97c3c8e21aea3d447addc7ace70bf2004c59d7b2e2c6eb0d8a9da6f38"
  },
  {
    "qId": "R4takken-037",
    "expectedBeforeStemSha256": "37c6562ba13543872c9e157808c446f4093ce6b5c1f59777efce89116d156d96",
    "replacementStemSha256": "f44f5dade2657a36757bb4fb7c8c3a259a44db9e8648916c439428ad69a5a184",
    "expectedLabelSequence": "ア・イ・ウ",
    "insertionOffsets": [
      81,
      211,
      330
    ],
    "sourceStatementCount": 3,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R4-q_a.pdf",
    "officialPdfSha256": "44baadbfaf0c5b3a872f107a4bc476d9c5a6516b3a6a0ca68678220c2271cf50",
    "pdfPage": 20,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2022/37.html",
    "sourceHash": "87e855f65072e4f0388df76210cb9c4e530e26412e45d3d50b316135a0397f0a"
  },
  {
    "qId": "R4takken-040",
    "expectedBeforeStemSha256": "3baae4d2807d9db0d3a542e1c658839f119f8db61c23572f5bedb4d2350fec10",
    "replacementStemSha256": "fcf3add8f3add0b8e17c8532e0e81271dacbd883b661fd4292762f8a9d774762",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      124,
      275,
      384,
      514
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R4-q_a.pdf",
    "officialPdfSha256": "44baadbfaf0c5b3a872f107a4bc476d9c5a6516b3a6a0ca68678220c2271cf50",
    "pdfPage": 22,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2022/40.html",
    "sourceHash": "98ecfa8fd72295063b28cf28cc09dab640713d185ffd9082d93f54fc49ae1e4f"
  },
  {
    "qId": "R4takken-041",
    "expectedBeforeStemSha256": "e9ca7d5baa4931e6e7349aea232394fc520942c1f72a4f739eaf49de7c0a2c2f",
    "replacementStemSha256": "cdec362f9d58dadf2459f23a574bf6354cfefe08cf208a7d80d45dcb85a15274",
    "expectedLabelSequence": "ア・イ・ウ・エ",
    "insertionOffsets": [
      82,
      211,
      332,
      448
    ],
    "sourceStatementCount": 4,
    "officialSourceUrl": "https://www.retio.or.jp/wp-content/uploads/2024/10/R4-q_a.pdf",
    "officialPdfSha256": "44baadbfaf0c5b3a872f107a4bc476d9c5a6516b3a6a0ca68678220c2271cf50",
    "pdfPage": 23,
    "sourceKind": "RETIO_official_question_pdf",
    "sourceRef": "https://takken-siken.com/kakomon/2022/41.html",
    "sourceHash": "b3fb5108daa11e2d93be2d72892d7d37173596f3607fb41f9756cf995935ead0"
  }
];

function ADMIN_patchTakkenStatementLabels_(options) {
  options = options || {};
  var apply = options.apply === true;
  if (options.dryRun === false && !apply) {
    throw new Error('dry-run is the default; use {apply:true} for explicit write');
  }
  if (apply) takkenStatementLabelRequireMaintenanceWindow_();
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var plan = takkenStatementLabelBuildPlan_();
    takkenStatementLabelAssertDb_(plan, 'plan');
    if (!apply) {
      plan.mode = 'dry-run';
      plan.wouldUpdate = plan.matched;
      return takkenStatementLabelReceipt_(plan);
    }
    if (plan.matched !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_ ||
        plan.nonTargetCount !== TAKKEN_STATEMENT_LABEL_PATCH_NON_TARGET_COUNT_) {
      throw new Error('fixed target/non-target count contract failed');
    }

    var patchId = 'takken-statement-labels-' + Utilities.getUuid();
    takkenStatementLabelAssertSpreadsheet_(plan, 'backup-before');
    var backupSheet = takkenStatementLabelEnsureBackupSheet_(plan.spreadsheet);
    var backupRows = plan.targets.map(function(target) {
      return [
        patchId, new Date(), 'prepared', plan.dbSpreadsheetId, target.qId, target.sheetRow, '',
        target.beforeRowSha256, target.afterRowSha256,
        plan.inventorySha256, plan.nonTargetInventorySha256, plan.inventoryOrderSha256,
        '', '', ''
      ].concat(target.beforeRow);
    });
    backupSheet.getRange(backupSheet.getLastRow() + 1, 1, backupRows.length, backupRows[0].length)
      .setValues(backupRows);
    SpreadsheetApp.flush();
    takkenStatementLabelAssertBackupComplete_(backupSheet, patchId, plan);
    takkenStatementLabelAssertDb_(plan, 'after-backup');

    try {
      var prewritePlan = takkenStatementLabelBuildPlan_();
      takkenStatementLabelAssertDb_(prewritePlan, 'prewrite');
      takkenStatementLabelAssertPlanSnapshot_(plan, prewritePlan);
      takkenStatementLabelAssertDb_(plan, 'api');
      takkenStatementLabelAssertDb_(prewritePlan, 'api');
      takkenStatementLabelBatchFindReplace_(prewritePlan, prewritePlan.targets.map(function(target) {
        return { find: target.beforeStem, replacement: target.afterStem };
      }));
      takkenStatementLabelClearQuestionCache_();
      takkenStatementLabelAssertDb_(prewritePlan, 'post-read');
      var post = takkenStatementLabelReadAndValidatePost_(prewritePlan, backupSheet, patchId);
      if (post.matched !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_ || post.updated !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_) {
        throw new Error('post-reread contract failed: matched=' + post.matched + ', updated=' + post.updated);
      }
      takkenStatementLabelSetBackupStatus_(backupSheet, patchId, 'applied');
      return {
        ok: true,
        mode: 'applied',
        patchId: patchId,
        matched: post.matched,
        updated: post.updated,
        nonTargetCount: prewritePlan.nonTargetCount,
        backupSheet: TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_SHEET_,
        targets: post.targets
      };
    } catch (writeError) {
      throw takkenStatementLabelHandleApplyFailure_(plan, backupSheet, patchId, writeError);
    }
  } finally {
    lock.releaseLock();
  }
}

// GASエディタRunボタン用の引数なしprivate wrapper。apply入口も明示名にする。
function ADMIN_patchTakkenStatementLabelsDryRun_() {
  return takkenStatementLabelEditorRun_('statement labels dry-run', function() {
    return ADMIN_patchTakkenStatementLabels_({ dryRun: true });
  });
}

function ADMIN_applyTakkenStatementLabels_() {
  return takkenStatementLabelEditorRun_('statement labels apply', function() {
    return ADMIN_patchTakkenStatementLabels_({ apply: true });
  });
}

function ADMIN_rollbackTakkenStatementLabels_(options) {
  options = options || {};
  var patchId = String(options.patchId || '').trim();
  if (!patchId) throw new Error('patchId is required');
  var apply = options.apply === true;
  if (options.dryRun === false && !apply) {
    throw new Error('rollback dry-run is the default; use {apply:true}');
  }
  if (apply) takkenStatementLabelRequireMaintenanceWindow_();
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var backupSheet = takkenStatementLabelEnsureBackupSheet_(null, false);
    var backup = takkenStatementLabelReadBackup_(backupSheet, patchId);
    if (backup.length !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_) {
      throw new Error('rollback requires exactly 51 backup rows: ' + backup.length);
    }
    var plan = takkenStatementLabelBuildPlanFromBackup_(backup);
    takkenStatementLabelAssertDb_(plan, 'rollback-plan');
    var current = takkenStatementLabelReadInventory_(plan.dbSpreadsheetId);
    takkenStatementLabelAssertDb_(plan, 'rollback-prewrite');
    takkenStatementLabelValidateState_(current, plan, 'after');
    if (!apply) {
      return { ok: true, mode: 'dry-run', patchId: patchId, matched: 51, wouldRestore: 51,
        nonTargetCount: plan.nonTargetCount, targets: plan.targets.map(takkenStatementLabelTargetReceipt_) };
    }
    try {
      takkenStatementLabelAssertDb_(plan, 'rollback-api');
      takkenStatementLabelBatchFindReplace_(plan, plan.targets.map(function(target) {
        return { find: target.afterStem, replacement: target.beforeStem };
      }));
      takkenStatementLabelClearQuestionCache_();
      takkenStatementLabelAssertDb_(plan, 'rollback-post-read');
      var post = takkenStatementLabelReadInventory_(plan.dbSpreadsheetId);
      takkenStatementLabelAssertDb_(plan, 'rollback-post-read-after');
      takkenStatementLabelValidateState_(post, plan, 'before');
      takkenStatementLabelSetBackupStatus_(backupSheet, patchId, 'rolled_back');
      return { ok: true, mode: 'rolled-back', patchId: patchId, matched: 51, restored: 51 };
    } catch (rollbackError) {
      try { takkenStatementLabelSetBackupStatus_(backupSheet, patchId, 'rollback_failed'); } catch (statusError) {}
      throw new Error('rollback failed; manual review required: ' + String(rollbackError.message || rollbackError));
    }
  } finally {
    lock.releaseLock();
  }
}

function ADMIN_rollbackLatestTakkenStatementLabelsDryRun_() {
  return takkenStatementLabelEditorRun_('statement labels rollback dry-run', function() {
    return ADMIN_rollbackTakkenStatementLabels_({ patchId: takkenStatementLabelLatestPatchId_(), dryRun: true });
  });
}

function ADMIN_rollbackLatestTakkenStatementLabels_() {
  return takkenStatementLabelEditorRun_('statement labels rollback apply', function() {
    return ADMIN_rollbackTakkenStatementLabels_({ patchId: takkenStatementLabelLatestPatchId_(), apply: true });
  });
}

function takkenStatementLabelReadInventory_(expectedDbId) {
  var configuredDbId = String(getDbId_() || '').trim();
  if (!configuredDbId) throw new Error('DB_SPREADSHEET_ID is missing; no mutation allowed');
  var spreadsheet = getDb_();
  var loadedDbId = String(spreadsheet.getId() || '').trim();
  if (!loadedDbId || loadedDbId !== configuredDbId) throw new Error('loaded Spreadsheet.getId does not match DB_SPREADSHEET_ID');
  if (expectedDbId && loadedDbId !== String(expectedDbId).trim()) throw new Error('loaded Spreadsheet object does not match expected plan DB');
  var sheet = spreadsheet.getSheetByName(SHEETS.QuestionBank);
  if (!sheet) throw new Error('QuestionBank sheet not found');
  var values = sheet.getDataRange().getValues();
  if (values.length <= 1) throw new Error('QuestionBank has no data rows');
  var headers = values[0].map(function(value, index) { return normalizeHeader_(value, index); });
  var expectedHeaders = HEADERS[SHEETS.QuestionBank];
  if (headers.join('\t') !== expectedHeaders.join('\t')) throw new Error('QuestionBank header mismatch; no mutation allowed');
  var headerIndex = {};
  headers.forEach(function(header, index) { headerIndex[header] = index; });
  var byId = {};
  var rowFingerprints = {};
  var orderedQIds = [];
  for (var rowIndex = 1; rowIndex < values.length; rowIndex++) {
    if (values[rowIndex].length !== headers.length) throw new Error('QuestionBank row width mismatch at row ' + (rowIndex + 1));
    var row = values[rowIndex].slice();
    var qId = String(row[headerIndex.qId] || '').trim();
    if (!qId) throw new Error('blank qId at row ' + (rowIndex + 1));
    if (Object.prototype.hasOwnProperty.call(byId, qId)) throw new Error('duplicate qId: ' + qId);
    byId[qId] = { row: row, sheetRow: rowIndex + 1 };
    rowFingerprints[qId] = { sheetRow: rowIndex + 1, rowSha256: takkenStatementLabelRowSha256_(row) };
    orderedQIds.push(qId);
  }
  var targetMap = takkenStatementLabelTargetMap_();
  return {
    spreadsheet: spreadsheet,
    spreadsheetId: loadedDbId,
    sheet: sheet,
    sheetId: sheet.getSheetId(),
    values: values,
    headers: headers,
    headerIndex: headerIndex,
    byId: byId,
    rowFingerprints: rowFingerprints,
    qIds: Object.keys(byId).sort(),
    orderedQIds: orderedQIds,
    stemColumnIndex: headerIndex.stem,
    inventorySha256: takkenStatementLabelInventorySha256_(rowFingerprints),
    nonTargetInventorySha256: takkenStatementLabelInventorySha256_(rowFingerprints, targetMap),
    inventoryOrderSha256: takkenStatementLabelSha256_(orderedQIds.join('\u001e'))
  };
}

function takkenStatementLabelTargetMap_() {
  var map = {};
  TAKKEN_STATEMENT_LABEL_PATCH_SPECS_.forEach(function(spec) { map[spec.qId] = true; });
  return map;
}

function takkenStatementLabelAssertDb_(plan, phase) {
  takkenStatementLabelAssertSpreadsheet_(plan, phase);
}

function takkenStatementLabelAssertSpreadsheet_(plan, phase) {
  var currentDbId = String(getDbId_() || '').trim();
  if (!plan || !plan.dbSpreadsheetId || currentDbId !== plan.dbSpreadsheetId) throw new Error('DB_SPREADSHEET_ID changed or is missing at ' + phase);
  var spreadsheet = getDb_();
  var loadedId = String(spreadsheet.getId() || '').trim();
  if (loadedId !== plan.dbSpreadsheetId) throw new Error('loaded Spreadsheet.getId changed at ' + phase);
  if (plan.spreadsheet && spreadsheet !== plan.spreadsheet) throw new Error('loaded Spreadsheet object changed at ' + phase);
  return spreadsheet;
}

function takkenStatementLabelInventorySha256_(rowFingerprints, excludedQIds) {
  excludedQIds = excludedQIds || {};
  var entries = Object.keys(rowFingerprints).filter(function(qId) { return !excludedQIds[qId]; }).sort().map(function(qId) {
    return qId + '\u001f' + rowFingerprints[qId].rowSha256;
  });
  return takkenStatementLabelSha256_(entries.join('\u001e'));
}

function takkenStatementLabelBuildPlan_() {
  if (TAKKEN_STATEMENT_LABEL_PATCH_SPECS_.length !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_) throw new Error('fixed statement label spec count must be 51');
  var dbSpreadsheetId = String(getDbId_() || '').trim();
  if (!dbSpreadsheetId) throw new Error('DB_SPREADSHEET_ID is missing; no mutation allowed');
  var inventory = takkenStatementLabelReadInventory_(dbSpreadsheetId);
  var targetMap = takkenStatementLabelTargetMap_();
  Object.keys(TAKKEN_STATEMENT_LABEL_PATCH_BLOCKED_QIDS_).forEach(function(qId) {
    if (targetMap[qId]) throw new Error('blocked or Q38 qId is in fixed target map: ' + qId);
  });
  var seen = {};
  var targets = TAKKEN_STATEMENT_LABEL_PATCH_SPECS_.map(function(spec) {
    if (seen[spec.qId]) throw new Error('duplicate fixed qId: ' + spec.qId);
    seen[spec.qId] = true;
    var rowInfo = inventory.byId[spec.qId];
    if (!rowInfo) throw new Error('target qId not found: ' + spec.qId);
    var beforeStem = takkenStatementLabelCanonicalText_(rowInfo.row[inventory.stemColumnIndex]);
    var afterStem = takkenStatementLabelBuildReplacementStem_(spec, beforeStem);
    takkenStatementLabelValidateSpec_(spec, beforeStem, afterStem, inventory);
    var beforeRow = rowInfo.row.slice();
    var afterRow = rowInfo.row.slice();
    afterRow[inventory.stemColumnIndex] = afterStem;
    return {
      qId: spec.qId,
      sheetRow: rowInfo.sheetRow,
      beforeStem: beforeStem,
      afterStem: afterStem,
      beforeRow: beforeRow,
      afterRow: afterRow,
      beforeRowSha256: takkenStatementLabelRowSha256_(beforeRow),
      afterRowSha256: takkenStatementLabelRowSha256_(afterRow),
      beforeStemSha256: takkenStatementLabelSha256_(beforeStem),
      afterStemSha256: takkenStatementLabelSha256_(afterStem),
      labelSequence: spec.expectedLabelSequence,
      officialPdfPage: spec.pdfPage
    };
  });
  if (targets.length !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_) throw new Error('matched must equal 51');
  if (Object.keys(inventory.byId).length !== 600) throw new Error('QuestionBank row count must equal 600');
  var nonTargetCount = Object.keys(inventory.byId).length - targets.length;
  if (nonTargetCount !== TAKKEN_STATEMENT_LABEL_PATCH_NON_TARGET_COUNT_) throw new Error('non-target count must equal 549');
  var expectedAfterFingerprints = {};
  Object.keys(inventory.rowFingerprints).forEach(function(qId) {
    expectedAfterFingerprints[qId] = { sheetRow: inventory.rowFingerprints[qId].sheetRow, rowSha256: inventory.rowFingerprints[qId].rowSha256 };
  });
  targets.forEach(function(target) { expectedAfterFingerprints[target.qId].rowSha256 = target.afterRowSha256; });
  return {
    ok: true,
    mode: 'plan',
    matched: targets.length,
    updated: 0,
    nonTargetCount: nonTargetCount,
    dbSpreadsheetId: dbSpreadsheetId,
    spreadsheet: inventory.spreadsheet,
    sheetId: inventory.sheetId,
    stemColumnIndex: inventory.stemColumnIndex,
    inventorySha256: inventory.inventorySha256,
    nonTargetInventorySha256: inventory.nonTargetInventorySha256,
    inventoryOrderSha256: inventory.inventoryOrderSha256,
    expectedAfterInventorySha256: takkenStatementLabelInventorySha256_(expectedAfterFingerprints),
    expectedAfterNonTargetInventorySha256: takkenStatementLabelInventorySha256_(expectedAfterFingerprints, targetMap),
    expectedAfterInventoryOrderSha256: inventory.inventoryOrderSha256,
    headerIndex: inventory.headerIndex,
    qIds: inventory.qIds,
    orderedQIds: inventory.orderedQIds,
    targets: targets,
    rowFingerprints: inventory.rowFingerprints
  };
}

function takkenStatementLabelBuildReplacementStem_(spec, beforeStem) {
  var offsets = spec.insertionOffsets.slice();
  var labels = spec.expectedLabelSequence.split('・');
  if (offsets.length !== labels.length || offsets.length !== Number(spec.sourceStatementCount)) throw new Error('offset/label count mismatch: ' + spec.qId);
  var parts = offsets.map(function(offset, index) { return { offset: Number(offset), label: labels[index] }; });
  parts.forEach(function(part) {
    if (!isFinite(part.offset) || part.offset < 0 || part.offset > beforeStem.length || Math.floor(part.offset) !== part.offset) throw new Error('insertion offset out of range: ' + spec.qId);
  });
  parts.sort(function(a, b) { return b.offset - a.offset; });
  var result = beforeStem;
  parts.forEach(function(part) { result = result.slice(0, part.offset) + '\n\n' + part.label + '\u3000' + result.slice(part.offset); });
  return result;
}

function takkenStatementLabelValidateSpec_(spec, beforeStem, afterStem, inventory) {
  if (takkenStatementLabelSha256_(beforeStem) !== spec.expectedBeforeStemSha256) throw new Error('expected-before stem hash mismatch: ' + spec.qId);
  if (takkenStatementLabelSha256_(afterStem) !== spec.replacementStemSha256) throw new Error('replacement stem hash mismatch: ' + spec.qId);
  var oldCounts = takkenStatementLabelCountStemOccurrences_(inventory, beforeStem);
  var newCounts = takkenStatementLabelCountStemOccurrences_(inventory, afterStem);
  if (oldCounts.exact !== 1 || oldCounts.substring !== 1) throw new Error('old stem must occur exactly once: ' + spec.qId);
  if (newCounts.exact !== 0 || newCounts.substring !== 0) throw new Error('replacement stem already exists: ' + spec.qId);
  spec.expectedLabelSequence.split('・').forEach(function(label) {
    if (afterStem.indexOf('\n\n' + label + '\u3000') < 0) throw new Error('expected label missing in replacement: ' + spec.qId);
  });
}

function takkenStatementLabelCountStemOccurrences_(inventory, needle) {
  var exact = 0;
  var substring = 0;
  Object.keys(inventory.byId).forEach(function(qId) {
    var stem = takkenStatementLabelCanonicalText_(inventory.byId[qId].row[inventory.stemColumnIndex]);
    if (stem === needle) exact++;
    var from = 0;
    while (true) {
      var at = stem.indexOf(needle, from);
      if (at < 0) break;
      substring++;
      from = at + Math.max(1, needle.length);
    }
  });
  return { exact: exact, substring: substring };
}

function takkenStatementLabelAssertPlanSnapshot_(before, after) {
  if (before.dbSpreadsheetId !== after.dbSpreadsheetId) throw new Error('DB_SPREADSHEET_ID changed between reads');
  takkenStatementLabelAssertDb_(before, 'plan-snapshot');
  if (before.spreadsheet !== after.spreadsheet || before.spreadsheetId !== after.spreadsheetId) throw new Error('Spreadsheet object or ID changed between reads');
  if (before.sheetId !== after.sheetId || before.stemColumnIndex !== after.stemColumnIndex) throw new Error('QuestionBank sheet identity or stem column changed');
  if (before.qIds.join('\t') !== after.qIds.join('\t') || before.orderedQIds.join('\t') !== after.orderedQIds.join('\t')) throw new Error('QuestionBank qId/order inventory changed between reads');
  before.qIds.forEach(function(qId) {
    if (!after.rowFingerprints[qId] || after.rowFingerprints[qId].sheetRow !== before.rowFingerprints[qId].sheetRow || after.rowFingerprints[qId].rowSha256 !== before.rowFingerprints[qId].rowSha256) {
      throw new Error('QuestionBank row/order changed between backup and write: ' + qId);
    }
  });
  before.targets.forEach(function(target) {
    var current = after.targets.find(function(candidate) { return candidate.qId === target.qId; });
    if (!current || current.beforeStemSha256 !== target.beforeStemSha256 || current.sheetRow !== target.sheetRow) throw new Error('target changed between backup and write: ' + target.qId);
  });
}

function takkenStatementLabelValidateState_(inventory, plan, state) {
  if (state !== 'before' && state !== 'after') throw new Error('invalid state: ' + state);
  if (inventory.qIds.join('\t') !== plan.qIds.join('\t') || inventory.orderedQIds.join('\t') !== plan.orderedQIds.join('\t')) throw new Error('QuestionBank qId/order inventory changed');
  var expectedFull = state === 'after' ? plan.expectedAfterInventorySha256 : plan.inventorySha256;
  var expectedNonTarget = state === 'after' ? plan.expectedAfterNonTargetInventorySha256 : plan.nonTargetInventorySha256;
  var expectedOrder = state === 'after' ? plan.expectedAfterInventoryOrderSha256 : plan.inventoryOrderSha256;
  if (inventory.inventorySha256 !== expectedFull || inventory.nonTargetInventorySha256 !== expectedNonTarget || inventory.inventoryOrderSha256 !== expectedOrder) throw new Error(state + ' inventory hash mismatch');
  var targetMap = takkenStatementLabelTargetMap_();
  plan.targets.forEach(function(target) {
    var current = inventory.byId[target.qId];
    if (!current || current.sheetRow !== target.sheetRow) throw new Error(state + ' target row/order mismatch: ' + target.qId);
    var expectedStem = state === 'after' ? target.afterStem : target.beforeStem;
    var forbiddenStem = state === 'after' ? target.beforeStem : target.afterStem;
    var currentStem = takkenStatementLabelCanonicalText_(current.row[inventory.stemColumnIndex]);
    var expectedCount = takkenStatementLabelCountStemOccurrences_(inventory, expectedStem);
    var forbiddenCount = takkenStatementLabelCountStemOccurrences_(inventory, forbiddenStem);
    if (expectedCount.exact !== 1 || expectedCount.substring !== 1 || forbiddenCount.exact !== 0 || forbiddenCount.substring !== 0) throw new Error(state + ' target stem occurrence mismatch: ' + target.qId);
    if (takkenStatementLabelSha256_(currentStem) !== takkenStatementLabelSha256_(expectedStem)) throw new Error(state + ' target stem hash mismatch: ' + target.qId);
    var expectedRowHash = state === 'after' ? target.afterRowSha256 : target.beforeRowSha256;
    if (takkenStatementLabelRowSha256_(current.row) !== expectedRowHash) throw new Error(state + ' target row hash mismatch: ' + target.qId);
    if (state === 'after') takkenStatementLabelAssertOnlyStemChanged_(target.beforeRow, current.row, inventory.stemColumnIndex, target.qId);
  });
  Object.keys(inventory.byId).forEach(function(qId) {
    if (!targetMap[qId] && (!plan.rowFingerprints[qId] || plan.rowFingerprints[qId].sheetRow !== inventory.byId[qId].sheetRow || plan.rowFingerprints[qId].rowSha256 !== takkenStatementLabelRowSha256_(inventory.byId[qId].row))) throw new Error('non-target row/order changed: ' + qId);
  });
  return { matched: plan.targets.length, updated: state === 'after' ? plan.targets.length : 0, targets: plan.targets.map(function(target) { return takkenStatementLabelTargetReceipt_(target); }) };
}

function takkenStatementLabelReadAndValidatePost_(plan, backupSheet, patchId) {
  takkenStatementLabelAssertDb_(plan, 'post-read-before');
  var inventory = takkenStatementLabelReadInventory_(plan.dbSpreadsheetId);
  takkenStatementLabelAssertDb_(plan, 'post-read-after');
  var result = takkenStatementLabelValidateState_(inventory, plan, 'after');
  takkenStatementLabelSetBackupPostState_(backupSheet, patchId, inventory);
  return result;
}

function takkenStatementLabelAssertOnlyStemChanged_(beforeRow, currentRow, stemIndex, qId) {
  if (beforeRow.length !== currentRow.length) throw new Error('row width changed: ' + qId);
  for (var i = 0; i < beforeRow.length; i++) {
    if (i !== stemIndex && takkenStatementLabelCellKey_(beforeRow[i]) !== takkenStatementLabelCellKey_(currentRow[i])) throw new Error('non-stem cell changed: ' + qId + ' column ' + i);
  }
}

function takkenStatementLabelEnsureBackupSheet_(spreadsheet, allowCreate) {
  allowCreate = allowCreate !== false;
  var ss = spreadsheet || getDb_();
  var sheet = ss.getSheetByName(TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_SHEET_);
  if (!sheet) {
    if (!allowCreate) throw new Error('backup sheet not found: ' + TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_SHEET_);
    sheet = ss.insertSheet(TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_SHEET_);
    sheet.getRange(1, 1, 1, TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.length).setValues([TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_]);
    sheet.setFrozenRows(1);
    return sheet;
  }
  var lastCol = Math.max(1, sheet.getLastColumn());
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(function(value, index) { return normalizeHeader_(value, index); });
  if (headers.join('\t') !== TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.join('\t')) throw new Error('statement label backup sheet header mismatch');
  return sheet;
}

function takkenStatementLabelSetBackupStatus_(sheet, patchId, status) {
  var data = sheet.getDataRange().getValues();
  var patchColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('patchId');
  var statusColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('patchStatus');
  for (var row = 1; row < data.length; row++) if (String(data[row][patchColumn]) === patchId) sheet.getRange(row + 1, statusColumn + 1).setValue(status);
}

function takkenStatementLabelSetBackupPostState_(sheet, patchId, inventory) {
  var data = sheet.getDataRange().getValues();
  var patchColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('patchId');
  var qIdColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('targetQId');
  var fullColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('afterInventorySha256');
  var nonTargetColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('afterNonTargetInventorySha256');
  var orderColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('afterInventoryOrderSha256');
  var rowColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('afterSourceRowNumber');
  for (var row = 1; row < data.length; row++) {
    if (String(data[row][patchColumn]) !== patchId) continue;
    var qId = String(data[row][qIdColumn] || '').trim();
    if (!inventory.byId[qId]) throw new Error('post state target missing in backup update: ' + qId);
    sheet.getRange(row + 1, fullColumn + 1).setValue(inventory.inventorySha256);
    sheet.getRange(row + 1, nonTargetColumn + 1).setValue(inventory.nonTargetInventorySha256);
    sheet.getRange(row + 1, orderColumn + 1).setValue(inventory.inventoryOrderSha256);
    sheet.getRange(row + 1, rowColumn + 1).setValue(inventory.byId[qId].sheetRow);
  }
}

function takkenStatementLabelReadBackup_(sheet, patchId) {
  var data = sheet.getDataRange().getValues();
  var headers = data[0].map(function(value, index) { return normalizeHeader_(value, index); });
  var index = {};
  headers.forEach(function(header, column) { index[header] = column; });
  return data.slice(1).filter(function(row) { return String(row[index.patchId] || '') === patchId; }).map(function(row) {
    var beforeRow = HEADERS[SHEETS.QuestionBank].map(function(header) { return row[index[header]]; });
    return {
      qId: String(row[index.targetQId] || '').trim(),
      dbSpreadsheetId: String(row[index.dbSpreadsheetId] || '').trim(),
      sourceRowNumber: Number(row[index.sourceRowNumber]),
      afterSourceRowNumber: Number(row[index.afterSourceRowNumber]),
      beforeRow: beforeRow,
      beforeRowSha256: String(row[index.beforeRowSha256] || ''),
      afterRowSha256: String(row[index.afterRowSha256] || ''),
      beforeInventorySha256: String(row[index.beforeInventorySha256] || ''),
      beforeNonTargetInventorySha256: String(row[index.beforeNonTargetInventorySha256] || ''),
      beforeInventoryOrderSha256: String(row[index.beforeInventoryOrderSha256] || ''),
      afterInventorySha256: String(row[index.afterInventorySha256] || ''),
      afterNonTargetInventorySha256: String(row[index.afterNonTargetInventorySha256] || ''),
      afterInventoryOrderSha256: String(row[index.afterInventoryOrderSha256] || '')
    };
  });
}

function takkenStatementLabelAssertBackupComplete_(sheet, patchId, plan) {
  var saved = takkenStatementLabelReadBackup_(sheet, patchId);
  if (saved.length !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_) throw new Error('backup verification requires 51 rows: ' + saved.length);
  var byId = {};
  saved.forEach(function(row) {
    if (byId[row.qId]) throw new Error('backup duplicate qId: ' + row.qId);
    byId[row.qId] = row;
  });
  plan.targets.forEach(function(target) {
    var savedTarget = byId[target.qId];
    if (!savedTarget || savedTarget.dbSpreadsheetId !== plan.dbSpreadsheetId || savedTarget.sourceRowNumber !== target.sheetRow ||
        savedTarget.beforeRowSha256 !== target.beforeRowSha256 || savedTarget.afterRowSha256 !== target.afterRowSha256 ||
        savedTarget.beforeInventorySha256 !== plan.inventorySha256 || savedTarget.beforeNonTargetInventorySha256 !== plan.nonTargetInventorySha256 ||
        savedTarget.beforeInventoryOrderSha256 !== plan.inventoryOrderSha256 || savedTarget.afterInventorySha256 !== '' ||
        savedTarget.afterNonTargetInventorySha256 !== '' || savedTarget.afterInventoryOrderSha256 !== '' ||
        takkenStatementLabelRowSha256_(savedTarget.beforeRow) !== target.beforeRowSha256) throw new Error('backup row/hash verification failed: ' + target.qId);
  });
}

function takkenStatementLabelBuildPlanFromBackup_(backup) {
  if (!backup || backup.length !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_) throw new Error('backup must contain 51 targets');
  var headerIndex = {};
  HEADERS[SHEETS.QuestionBank].forEach(function(header, index) { headerIndex[header] = index; });
  var seen = {};
  var targets = backup.map(function(row) {
    if (seen[row.qId]) throw new Error('duplicate backup qId: ' + row.qId);
    seen[row.qId] = true;
    if (TAKKEN_STATEMENT_LABEL_PATCH_BLOCKED_QIDS_[row.qId]) throw new Error('blocked/Q38 qId in backup: ' + row.qId);
    var spec = TAKKEN_STATEMENT_LABEL_PATCH_SPECS_.find(function(candidate) { return candidate.qId === row.qId; });
    if (!spec) throw new Error('backup qId is outside fixed allowlist: ' + row.qId);
    var beforeRow = row.beforeRow.slice();
    if (beforeRow.length !== HEADERS[SHEETS.QuestionBank].length || takkenStatementLabelRowSha256_(beforeRow) !== row.beforeRowSha256) throw new Error('backup before-row hash mismatch: ' + row.qId);
    var beforeStem = takkenStatementLabelCanonicalText_(beforeRow[headerIndex.stem]);
    var afterStem = takkenStatementLabelBuildReplacementStem_(spec, beforeStem);
    if (takkenStatementLabelSha256_(afterStem) !== spec.replacementStemSha256) throw new Error('backup replacement hash mismatch: ' + row.qId);
    var afterRow = beforeRow.slice();
    afterRow[headerIndex.stem] = afterStem;
    if (takkenStatementLabelRowSha256_(afterRow) !== row.afterRowSha256) throw new Error('backup after-row hash mismatch: ' + row.qId);
    return { qId: row.qId, sheetRow: row.afterSourceRowNumber || row.sourceRowNumber, beforeStem: beforeStem, afterStem: afterStem, beforeRow: beforeRow, afterRow: afterRow, beforeRowSha256: row.beforeRowSha256, afterRowSha256: row.afterRowSha256, beforeStemSha256: takkenStatementLabelSha256_(beforeStem), afterStemSha256: takkenStatementLabelSha256_(afterStem) };
  });
  var dbId = String(backup[0].dbSpreadsheetId || '').trim();
  if (!dbId) throw new Error('backup has no DB_SPREADSHEET_ID');
  backup.forEach(function(row) {
    if (row.dbSpreadsheetId !== dbId || row.beforeInventorySha256 !== backup[0].beforeInventorySha256 || row.beforeNonTargetInventorySha256 !== backup[0].beforeNonTargetInventorySha256 || row.beforeInventoryOrderSha256 !== backup[0].beforeInventoryOrderSha256 || row.afterInventorySha256 !== backup[0].afterInventorySha256 || row.afterNonTargetInventorySha256 !== backup[0].afterNonTargetInventorySha256 || row.afterInventoryOrderSha256 !== backup[0].afterInventoryOrderSha256) throw new Error('backup inventory metadata mismatch');
  });
  if (!backup[0].afterInventorySha256 || !backup[0].afterNonTargetInventorySha256 || !backup[0].afterInventoryOrderSha256) throw new Error('backup has no post-apply inventory baseline');
  if (String(getDbId_() || '').trim() !== dbId) throw new Error('DB_SPREADSHEET_ID does not match backup');
  var inventory = takkenStatementLabelReadInventory_(dbId);
  if (inventory.inventorySha256 !== backup[0].afterInventorySha256 || inventory.nonTargetInventorySha256 !== backup[0].afterNonTargetInventorySha256 || inventory.inventoryOrderSha256 !== backup[0].afterInventoryOrderSha256) throw new Error('post-apply inventory/order drift detected before rollback');
  targets.forEach(function(target) { if (inventory.byId[target.qId].sheetRow !== target.sheetRow) throw new Error('target row/order drift detected before rollback: ' + target.qId); });
  var targetMap = takkenStatementLabelTargetMap_();
  return {
    ok: true,
    mode: 'rollback-plan',
    matched: targets.length,
    updated: 0,
    nonTargetCount: TAKKEN_STATEMENT_LABEL_PATCH_NON_TARGET_COUNT_,
    dbSpreadsheetId: dbId,
    spreadsheet: inventory.spreadsheet,
    sheetId: inventory.sheetId,
    stemColumnIndex: inventory.stemColumnIndex,
    inventorySha256: backup[0].beforeInventorySha256,
    nonTargetInventorySha256: backup[0].beforeNonTargetInventorySha256,
    inventoryOrderSha256: backup[0].beforeInventoryOrderSha256,
    expectedAfterInventorySha256: backup[0].afterInventorySha256,
    expectedAfterNonTargetInventorySha256: backup[0].afterNonTargetInventorySha256,
    expectedAfterInventoryOrderSha256: backup[0].afterInventoryOrderSha256,
    qIds: inventory.qIds,
    orderedQIds: inventory.orderedQIds,
    targets: targets,
    rowFingerprints: inventory.rowFingerprints,
    targetMap: targetMap
  };
}

function takkenStatementLabelBatchFindReplace_(plan, replacements) {
  takkenStatementLabelAssertSpreadsheet_(plan, 'api-batchUpdate');
  if (typeof Sheets === 'undefined' || !Sheets.Spreadsheets || typeof Sheets.Spreadsheets.batchUpdate !== 'function') throw new Error('Advanced Sheets service unavailable; no fallback is permitted');
  if (!plan || plan.matched !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_ || plan.sheetId === undefined || plan.stemColumnIndex === undefined) throw new Error('invalid fixed statement label plan');
  if (!replacements || replacements.length !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_) throw new Error('exactly 51 findReplace requests are required');
  var seenFind = {};
  var seenReplacement = {};
  var requests = replacements.map(function(replacement) {
    var find = takkenStatementLabelCanonicalText_(replacement.find);
    var replaceWith = takkenStatementLabelCanonicalText_(replacement.replacement);
    if (!find || !replaceWith || find === replaceWith || seenFind[find] || seenReplacement[replaceWith]) throw new Error('invalid or duplicate exact stem replacement');
    seenFind[find] = true;
    seenReplacement[replaceWith] = true;
    return { findReplace: {
      find: find,
      replacement: replaceWith,
      matchCase: true,
      matchEntireCell: true,
      searchByRegex: false,
      includeFormulas: false,
      range: { sheetId: plan.sheetId, startColumnIndex: plan.stemColumnIndex, endColumnIndex: plan.stemColumnIndex + 1 }
    } };
  });
  var response = Sheets.Spreadsheets.batchUpdate({ requests: requests, includeSpreadsheetInResponse: false }, plan.dbSpreadsheetId);
  var replies = response && response.replies;
  if (!replies || replies.length !== TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_) throw new Error('Sheets batchUpdate reply count mismatch');
  replies.forEach(function(reply, index) {
    var count = reply && reply.findReplace && Number(reply.findReplace.occurrencesChanged);
    if (count !== 1) throw new Error('occurrencesChanged must equal 1 for request ' + (index + 1) + ': ' + count);
  });
  return { requests: TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_, occurrencesChanged: TAKKEN_STATEMENT_LABEL_PATCH_TARGET_COUNT_ };
}

function takkenStatementLabelClassifyState_(inventory, plan) {
  var before = true;
  var after = true;
  plan.targets.forEach(function(target) {
    var current = inventory.byId[target.qId];
    if (!current) { before = false; after = false; return; }
    var stem = takkenStatementLabelCanonicalText_(current.row[inventory.stemColumnIndex]);
    if (stem !== target.beforeStem) before = false;
    if (stem !== target.afterStem) after = false;
  });
  if (before) return 'before';
  if (after) return 'after';
  var anyBefore = false;
  var anyAfter = false;
  plan.targets.forEach(function(target) {
    var current = inventory.byId[target.qId];
    if (!current) return;
    var stem = takkenStatementLabelCanonicalText_(current.row[inventory.stemColumnIndex]);
    anyBefore = anyBefore || stem === target.beforeStem;
    anyAfter = anyAfter || stem === target.afterStem;
  });
  if (anyBefore && anyAfter) return 'partial';
  return 'unknown';
}

function takkenStatementLabelHandleApplyFailure_(plan, backupSheet, patchId, writeError) {
  var message = String(writeError && writeError.message || writeError || 'unknown write error');
  var current;
  try { current = takkenStatementLabelReadInventory_(plan.dbSpreadsheetId); }
  catch (readError) {
    try { takkenStatementLabelSetBackupStatus_(backupSheet, patchId, 'manual_review'); } catch (statusError) {}
    return new Error('apply response/state is unknown; manual review required: ' + message + '; reread failed: ' + String(readError.message || readError));
  }
  var state = takkenStatementLabelClassifyState_(current, plan);
  if (state === 'before') {
    try { takkenStatementLabelValidateState_(current, plan, 'before'); } catch (beforeError) { try { takkenStatementLabelSetBackupStatus_(backupSheet, patchId, 'manual_review'); } catch (statusError1) {} return new Error('pre-write state could not be verified; manual review required: ' + message); }
    try { takkenStatementLabelSetBackupStatus_(backupSheet, patchId, 'not_applied'); } catch (statusError2) {}
    return new Error('apply failed; no QuestionBank mutation verified: ' + message);
  }
  if (state === 'after') {
    try {
      takkenStatementLabelValidateState_(current, plan, 'after');
      takkenStatementLabelBatchFindReplace_(plan, plan.targets.map(function(target) { return { find: target.afterStem, replacement: target.beforeStem }; }));
      takkenStatementLabelClearQuestionCache_();
      var restored = takkenStatementLabelReadInventory_(plan.dbSpreadsheetId);
      takkenStatementLabelValidateState_(restored, plan, 'before');
      takkenStatementLabelSetBackupStatus_(backupSheet, patchId, 'rolled_back');
      return new Error('apply failed; exact automatic rollback verified: ' + message);
    } catch (rollbackError) {
      try { takkenStatementLabelSetBackupStatus_(backupSheet, patchId, 'rollback_failed'); } catch (statusError3) {}
      return new Error('apply failed; rollback failed; manual review required: ' + message + '; ' + String(rollbackError.message || rollbackError));
    }
  }
  try { takkenStatementLabelSetBackupStatus_(backupSheet, patchId, state === 'partial' ? 'partial' : 'manual_review'); } catch (statusError4) {}
  return new Error('apply state is ' + state + '; no automatic rollback attempted; manual review required: ' + message);
}

function takkenStatementLabelRequireMaintenanceWindow_() {
  var props = getScriptProps_();
  var value = props && props.getProperty(TAKKEN_STATEMENT_LABEL_PATCH_MAINTENANCE_PROPERTY_);
  if (String(value || '').toUpperCase() !== 'OPEN') throw new Error('maintenance window is not OPEN; set ' + TAKKEN_STATEMENT_LABEL_PATCH_MAINTENANCE_PROPERTY_ + '=OPEN only during approved maintenance');
}

function takkenStatementLabelClearQuestionCache_() {
  if (typeof clearAllCache_ !== 'function') throw new Error('strict question cache invalidator is unavailable');
  clearAllCache_({ strict: true });
}

function takkenStatementLabelLatestPatchId_() {
  var sheet = takkenStatementLabelEnsureBackupSheet_(null, false);
  var data = sheet.getDataRange().getValues();
  var patchColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('patchId');
  var statusColumn = TAKKEN_STATEMENT_LABEL_PATCH_BACKUP_HEADERS_.indexOf('patchStatus');
  for (var row = data.length - 1; row >= 1; row--) if (String(data[row][statusColumn] || '') === 'applied' && String(data[row][patchColumn] || '')) return String(data[row][patchColumn]);
  throw new Error('no applied statement label patch backup is available');
}

function takkenStatementLabelTargetReceipt_(target) {
  return { qId: target.qId, sheetRow: target.sheetRow, beforeStemSha256: target.beforeStemSha256, afterStemSha256: target.afterStemSha256, beforeRowSha256: target.beforeRowSha256, afterRowSha256: target.afterRowSha256, labelSequence: target.labelSequence };
}

function takkenStatementLabelReceipt_(result) {
  var safe = {};
  ['ok', 'mode', 'patchId', 'matched', 'updated', 'wouldUpdate', 'restored', 'wouldRestore', 'nonTargetCount', 'backupSheet'].forEach(function(key) { if (result[key] !== undefined) safe[key] = result[key]; });
  if (result.targets) safe.targets = result.targets.map(takkenStatementLabelTargetReceipt_);
  return safe;
}

function takkenStatementLabelEditorRun_(label, callback) {
  try {
    var result = callback();
    if (typeof Logger !== 'undefined' && Logger.log) Logger.log(label + ': ' + JSON.stringify(takkenStatementLabelReceipt_(result)));
    return result;
  } catch (error) {
    if (typeof Logger !== 'undefined' && Logger.log) Logger.log(label + ' ERROR: ' + String(error.message || error));
    throw error;
  }
}

function takkenStatementLabelCanonicalText_(value) {
  return String(value == null ? '' : value).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

function takkenStatementLabelCellKey_(value) {
  if (Object.prototype.toString.call(value) === '[object Date]') return 'date:' + value.toISOString();
  return typeof value + ':' + String(value == null ? '' : value);
}

function takkenStatementLabelRowSha256_(row) {
  return takkenStatementLabelSha256_(row.map(takkenStatementLabelCellKey_).join('\u001f'));
}

function takkenStatementLabelSha256_(value) {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(value), Utilities.Charset.UTF_8);
  return bytes.map(function(byte) { var number = byte < 0 ? byte + 256 : byte; return (number < 16 ? '0' : '') + number.toString(16); }).join('');
}
