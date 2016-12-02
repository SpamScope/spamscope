function PadSpaceRight(str, len) {
    str = str + ""; // Force to string.
    if (str.length < len)
        str = str + Array(len + 1 - str.length).join(" ");
    return str;
}
var tagString;
var folderEnum = DOpus.FSUtil.ReadDir("C:\\", false);
while (!folderEnum.complete) {
    var folderItem = folderEnum.next;
    if (!folderItem.is_dir) {
        if (folderItem.metadata == "none") {
            tagString = "<no metadata available>";
        } else {
            tagString = "";
            for (var tagEnum = new Enumerator(folderItem.metadata.tags); !tagEnum.atEnd(); tagEnum.moveNext()) {
                if (tagString != "") {
                    tagString += ", ";
                    tagString += tagEnum.item();
                } else {
                    tagString = tagEnum.item();
                }
            }
            if (tagString == "") {
                tagString = "<no tags>";
            }
        }
        DOpus.Output(PadSpaceRight(folderItem + ": ", 25) + tagString);
    }
}
