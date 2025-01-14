from transformers import AutoModelForSequenceClassification, AutoTokenizer

class ResponseFilter():
    FILTERED_MESSAGE = "Filtered..."
    GOOD_LABEL = "OK"
    model = AutoModelForSequenceClassification.from_pretrained("KoalaAI/Text-Moderation")
    tokenizer = AutoTokenizer.from_pretrained("KoalaAI/Text-Moderation")

    def __call__(self, response):
        label = self.get_response_type(response)
        if label != self.GOOD_LABEL:
            return self.FILTERED_MESSAGE
        return response

    def get_response_type(self, response):
        # Run the model on your input
        inputs = self.tokenizer(response, return_tensors="pt")
        outputs = self.model(**inputs)

        # Get the predicted logits
        logits = outputs.logits

        # Apply softmax to get probabilities (scores)
        probabilities = logits.softmax(dim=-1).squeeze()

        # Retrieve the labels
        id2label = self.model.config.id2label
        labels = [id2label[idx] for idx in range(len(probabilities))]

        # Combine labels and probabilities, then sort
        label_prob_pairs = list(zip(labels, probabilities))
        label_prob_pairs.sort(key=lambda item: item[1], reverse=True)  

        top_label, _ = label_prob_pairs[0]
        return top_label