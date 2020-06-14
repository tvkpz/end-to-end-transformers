import json
import torch
from torch import nn
from transformers import BertModel, BertTokenizer

JSON_CONTENT_TYPE = 'application/json'
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
PRE_TRAINED_MODEL_NAME = 'bert-base-cased'
CLASS_NAMES = ['negative', 'neutral', 'positive']

class SentimentClassifier(nn.Module):

    def __init__(self, n_classes):
        super(SentimentClassifier, self).__init__()
        self.bert = BertModel.from_pretrained(PRE_TRAINED_MODEL_NAME)
        self.drop = nn.Dropout(p=0.3)
        self.out = nn.Linear(self.bert.config.hidden_size, n_classes)

    def forward(self, input_ids, attention_mask):
        _, pooled_output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        output = self.drop(pooled_output)
        return self.out(output)


# defines the model
def model_fn(model_dir):
    model_path = f'{model_dir}/best_model.bin'
    model = SentimentClassifier(len(CLASS_NAMES))
    model.load_state_dict(torch.load(model_path))
    model = model.to(DEVICE)
    return model

# Perform prediction on the deserialized object, with the loaded model
def predict_fn(input_data, model):
    MAX_LEN = 160
    tokenizer = BertTokenizer.from_pretrained(PRE_TRAINED_MODEL_NAME)
    
    review_text = input_data['text']
    
    encoded_review = tokenizer.encode_plus(
      review_text,
      max_length=MAX_LEN,
      add_special_tokens=True,
      return_token_type_ids=False,
      pad_to_max_length=True,
      return_attention_mask=True,
      return_tensors='pt',
    )
    input_ids = encoded_review['input_ids'].to(DEVICE)
    attention_mask = encoded_review['attention_mask'].to(DEVICE)

    output = model(input_ids, attention_mask)
    _, prediction = torch.max(output, dim=1)
    return prediction


def input_fn(serialized_input_data, content_type=JSON_CONTENT_TYPE):  
    if content_type == JSON_CONTENT_TYPE:
        input_data = json.loads(serialized_input_data)
        return input_data
    else:
        pass

def output_fn(prediction_output, accept=JSON_CONTENT_TYPE):
    if accept == JSON_CONTENT_TYPE:
        return json.dumps(prediction_output), accept
    raise Exception('Requested unsupported ContentType in Accept: ' + accept)