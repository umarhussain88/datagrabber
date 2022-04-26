// google app script

function removeLabels(label_name) {
    var myLabel = GmailApp.getUserLabelByName(label_name);
    var processedLabel = GmailApp.getUserLabelByName("Processed");
    console.log(myLabel.getName())
    var threads = myLabel.getThreads();
    for (var x in threads) {
        var thread = threads[x];
        thread.markRead();
        thread.removeLabel(myLabel);
        thread.addLabel(processedLabel);
    }
}

// get latest emails from gmail
function getLatestEmails() {
    var threads = GmailApp.search(query = "label:data---new-card-bing")
    var emails = threads[0].getMessages();
    var attachments = [];
    // get xlsx attachments
    for (var i = 0; i < emails.length; i++) {
        var email = emails[i];
        var attachments = email.getAttachments();
        for (var j = 0; j < attachments.length; j++) {
            var attachment = attachments[j];
            if (attachment.getName().indexOf(".xlsx") > -1) {
                // download file to drive to folder
                
                var file = DriveApp.createFile(attachment.getName(), attachment.getAs("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"));
                // move file to folder
                folder = DriveApp.getFolderById('1ztzaH9Hv-ONjwh9tw7o-sEDY6R9WCWaf')
                file.moveTo(folder);


            }

        }
    }
    removeLabels('data---new-card-bing')
}
